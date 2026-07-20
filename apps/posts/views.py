from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseForbidden

from django.db.models import Prefetch
from apps.votes.models import PostVote, CommentVote
from .models import Post
from .forms import PostCreateForm


class CachedReplies:
    """
    Вспомогательный класс для кэширования ответов комментариев,
    чтобы избежать N+1 запросов при обращении к comment.replies.all/exists в шаблоне.
    """
    def __init__(self, replies):
        self._replies = replies

    def all(self):
        return self._replies

    def exists(self):
        return len(self._replies) > 0


class HomeView(ListView):
    model = Post
    template_name = 'posts/home.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        qs = Post.objects.filter(is_deleted=False).select_related('author', 'community').order_by('-created_at')
        if self.request.user.is_authenticated:
            user_votes = PostVote.objects.filter(user=self.request.user)
            qs = qs.prefetch_related(Prefetch('votes', queryset=user_votes, to_attr='user_votes'))
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Добавляем user_vote к постам
        if self.request.user.is_authenticated:
            for post in context['posts']:
                post.user_vote = post.user_votes[0].value if getattr(post, 'user_votes', None) else None
        else:
            for post in context['posts']:
                post.user_vote = None
        
        # Популярные сообщества для сайдбара
        from apps.communities.models import Community
        context['popular_communities'] = Community.objects.all().order_by('-member_count')[:10]
        
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = 'posts/detail.html'
    context_object_name = 'post'
    
    def get_object(self, queryset=None):
        community_slug = self.kwargs.get('community_slug')
        post_id = self.kwargs.get('post_id')

        qs = Post.objects.select_related('author', 'community')
        if self.request.user.is_authenticated:
            user_votes = PostVote.objects.filter(user=self.request.user)
            qs = qs.prefetch_related(Prefetch('votes', queryset=user_votes, to_attr='user_votes'))

        return get_object_or_404(
            qs,
            id=post_id,
            community__slug=community_slug,
            is_deleted=False
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        
        # Голос пользователя за пост
        if self.request.user.is_authenticated:
            context['user_vote'] = post.user_votes[0].value if getattr(post, 'user_votes', None) else None
        else:
            context['user_vote'] = None
        
        # Комментарии верхнего уровня с user_vote
        comments_qs = post.comments.select_related('author')
        if self.request.user.is_authenticated:
            user_votes = CommentVote.objects.filter(user=self.request.user)
            comments_qs = comments_qs.prefetch_related(Prefetch('votes', queryset=user_votes, to_attr='user_votes'))

        all_comments = list(comments_qs.order_by('created_at'))

        # Устанавливаем user_vote для каждого комментария
        for comment in all_comments:
            comment.user_vote = comment.user_votes[0].value if getattr(comment, 'user_votes', None) else None

        # Структурируем древовидную структуру в памяти
        replies_map = {c.id: [] for c in all_comments}
        for c in all_comments:
            if c.parent_id and c.parent_id in replies_map:
                replies_map[c.parent_id].append(c)

        # Рекурсивный хелпер для проверки наличия неудалённых ответов
        def has_non_deleted_descendants(comment_id):
            for reply in replies_map.get(comment_id, []):
                if not reply.is_deleted or has_non_deleted_descendants(reply.id):
                    return True
            return False

        # Заполняем CachedReplies для каждого комментария
        for c in all_comments:
            all_replies = replies_map.get(c.id, [])
            active_replies = []
            for reply in all_replies:
                if not reply.is_deleted or has_non_deleted_descendants(reply.id):
                    active_replies.append(reply)
            c._cached_replies = CachedReplies(active_replies)

        # Временно подменяем дескриптор replies класса Comment
        from apps.comments.models import Comment as CommentModel
        original_descriptor = CommentModel.replies
        
        def get_replies(self_comment):
            if hasattr(self_comment, '_cached_replies'):
                return self_comment._cached_replies
            return original_descriptor.__get__(self_comment, CommentModel)

        CommentModel.replies = property(get_replies)
        
        try:
            # Выбираем только корневые комментарии (parent_id is None)
            root_comments = []
            for c in all_comments:
                if c.parent_id is None:
                    if not c.is_deleted or has_non_deleted_descendants(c.id):
                        root_comments.append(c)

            context['comments'] = root_comments
        finally:
            # Восстанавливаем оригинальный дескриптор
            CommentModel.replies = original_descriptor
        
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostCreateForm
    template_name = 'posts/create.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Пост создан! 🎉')
        return super().form_valid(form)
    
    def get_success_url(self):
        return self.object.get_absolute_url()


@login_required
def post_delete_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    is_moderator = post.community.members.filter(
        user=request.user,
        role__in=['moderator', 'admin']
    ).exists()
    
    if post.author != request.user and not is_moderator and not request.user.is_staff:
        return HttpResponseForbidden('У вас нет прав для удаления этого поста.')
    
    post.is_deleted = True
    post.save()
    messages.success(request, 'Пост удалён.')
    return redirect('posts:home')
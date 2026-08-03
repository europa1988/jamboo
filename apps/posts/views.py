from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseForbidden

from .models import Post
from .forms import PostCreateForm


class HomeView(ListView):
    model = Post
    template_name = 'posts/home.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        return Post.objects.filter(is_deleted=False).select_related(
            'author', 'community'
        ).prefetch_related('votes').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Добавляем user_vote к постам
        if self.request.user.is_authenticated:
            for post in context['posts']:
                post.user_vote = post.get_user_vote(self.request.user)
        
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
        return get_object_or_404(
            Post.objects.select_related('author', 'community'),
            id=post_id,
            community__slug=community_slug,
            is_deleted=False
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        
        # Голос пользователя за пост
        context['user_vote'] = post.get_user_vote(self.request.user)
        
        # Комментарии верхнего уровня с user_vote (сохраняем целостность дерева комментариев)
        from django.db.models import Q
        comments = post.comments.filter(
            parent__isnull=True
        ).filter(
            Q(is_deleted=False) | Q(replies__isnull=False)
        ).distinct().select_related('author').prefetch_related('replies', 'votes')
        
        # Добавляем user_vote к каждому комментарию
        for comment in comments:
            comment.user_vote = comment.get_user_vote(self.request.user)
            # Рекурсивно добавляем к ответам
            self._add_votes_to_replies(comment, self.request.user)
        
        context['comments'] = comments
        
        return context
    
    def _add_votes_to_replies(self, comment, user):
        """Рекурсивно добавляет user_vote к ответам."""
        for reply in comment.replies.all():
            reply.user_vote = reply.get_user_vote(user)
            self._add_votes_to_replies(reply, user)


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
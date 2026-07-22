from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseForbidden

from .models import Post
from .forms import PostCreateForm
from apps.comments.models import Comment

original_replies_descriptor = Comment.replies


class CustomRepliesDescriptor:
    def __init__(self, original):
        self.original = original

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if hasattr(instance, '_precalculated_replies'):
            class MockManager:
                def __init__(self, replies_list):
                    self.replies_list = replies_list
                def all(self):
                    return self.replies_list
            return MockManager(instance._precalculated_replies)
        return self.original.__get__(instance, owner)


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
    
    def get(self, request, *args, **kwargs):
        Comment.replies = CustomRepliesDescriptor(original_replies_descriptor)
        try:
            return super().get(request, *args, **kwargs)
        finally:
            Comment.replies = original_replies_descriptor

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
        
        # Получаем все комментарии для поста (включая удалённые)
        all_comments = list(post.comments.all().select_related('author').prefetch_related('votes'))
        
        comment_by_id = {c.id: c for c in all_comments}
        children_map = {}
        for c in all_comments:
            if c.parent_id:
                children_map.setdefault(c.parent_id, []).append(c)

        has_active_descendants_cache = {}

        def has_active_descendant(comment_id):
            if comment_id in has_active_descendants_cache:
                return has_active_descendants_cache[comment_id]

            for child in children_map.get(comment_id, []):
                if not child.is_deleted:
                    has_active_descendants_cache[comment_id] = True
                    return True
                if has_active_descendant(child.id):
                    has_active_descendants_cache[comment_id] = True
                    return True

            has_active_descendants_cache[comment_id] = False
            return False

        # Оставляем только те комментарии, которые либо не удалены, либо имеют неудалённые ответы
        keep_comments = [c for c in all_comments if not c.is_deleted or has_active_descendant(c.id)]
        keep_comments_set = set(keep_comments)
        
        for c in keep_comments:
            child_replies = [child for child in children_map.get(c.id, []) if child in keep_comments_set]
            child_replies.sort(key=lambda x: x.created_at)
            c._precalculated_replies = child_replies
            c.user_vote = c.get_user_vote(self.request.user)

        comments = [c for c in keep_comments if c.parent_id is None]
        comments.sort(key=lambda x: x.created_at)
        
        context['comments'] = comments
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
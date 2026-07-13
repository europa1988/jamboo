from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.template.loader import render_to_string

from .forms import RegisterForm, LoginForm, ProfileEditForm
from .models import User, UserFollow


def register_view(request):
    """
    Регистрация нового пользователя.
    """
    if request.user.is_authenticated:
        return redirect('posts:home')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Добро пожаловать в Jamboo!')
            return redirect('posts:home')
        else:
            messages.error(request, 'Исправьте ошибки в форме.')
    else:
        form = RegisterForm()
    
    return render(request, 'users/register.html', {
        'form': form,
        'title': 'Регистрация'
    })


def login_view(request):
    """
    Вход в аккаунт.
    """
    if request.user.is_authenticated:
        return redirect('posts:home')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'С возвращением, {user.username}!')
            
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('posts:home')
        else:
            messages.error(request, 'Неверный никнейм или пароль.')
    else:
        form = LoginForm()
    
    return render(request, 'users/login.html', {
        'form': form,
        'title': 'Вход'
    })


def logout_view(request):
    """
    Выход из аккаунта.
    """
    logout(request)
    messages.success(request, 'Вы успешно вышли. До встречи!')
    return redirect('posts:home')


class ProfileView(DetailView):
    """
    Страница профиля пользователя.
    """
    model = User
    template_name = 'users/profile.html'
    context_object_name = 'profile_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        
        # Посты пользователя (с user_vote для текущего просматривающего)
        posts = user.posts.filter(is_deleted=False).select_related('community').prefetch_related('votes').order_by('-created_at')[:20]
        if self.request.user.is_authenticated:
            for post in posts:
                post.user_vote = post.get_user_vote(self.request.user)
        context['user_posts'] = posts
        
        # Комментарии пользователя
        comments = user.comments.filter(is_deleted=False).select_related('post__community').order_by('-created_at')[:20]
        if self.request.user.is_authenticated:
            for comment in comments:
                comment.user_vote = comment.get_user_vote(self.request.user)
        context['user_comments'] = comments
        
        # Подписки
        context['following_count'] = user.following.count()
        context['followers_count'] = user.followers.count()
        
        # Проверяем, подписан ли текущий пользователь
        context['is_following'] = False
        if self.request.user.is_authenticated and self.request.user != user:
            context['is_following'] = UserFollow.objects.filter(
                follower=self.request.user,
                following=user
            ).exists()
        
        # Карма
        context['post_karma'] = sum(p.score for p in user.posts.all())
        context['comment_karma'] = sum(c.score for c in user.comments.all())
        
        # Активная вкладка (posts или comments)
        context['active_tab'] = self.request.GET.get('tab', 'posts')
        
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """
    Редактирование профиля.
    """
    model = User  # Будем работать через User, но форма для профиля
    form_class = ProfileEditForm
    template_name = 'users/settings.html'
    
    def get_object(self, queryset=None):
        return self.request.user.profile
    
    def get_success_url(self):
        return reverse_lazy('users:profile', kwargs={'username': self.request.user.username})
    
    def form_valid(self, form):
        messages.success(self.request, 'Профиль обновлен!')
        return super().form_valid(form)


@login_required
def follow_user(request, username):
    """
    Подписка/отписка на пользователя (HTMX).
    """
    target_user = get_object_or_404(User, username=username)
    
    if target_user == request.user:
        return HttpResponse('Нельзя подписаться на себя', status=400)
    
    follow_obj = UserFollow.objects.filter(
        follower=request.user,
        following=target_user
    ).first()
    
    if follow_obj:
        follow_obj.delete()
        is_following = False
    else:
        UserFollow.objects.create(
            follower=request.user,
            following=target_user
        )
        is_following = True
    
    html = render_to_string('users/partials/follow_button.html', {
        'profile_user': target_user,
        'is_following': is_following
    }, request=request)
    
    return HttpResponse(html)


@login_required
def user_posts(request, username):
    """
    Все посты пользователя (для HTMX подгрузки).
    """
    user = get_object_or_404(User, username=username)
    posts = user.posts.filter(is_deleted=False).select_related('community').prefetch_related('votes').order_by('-created_at')
    
    if request.user.is_authenticated:
        for post in posts:
            post.user_vote = post.get_user_vote(request.user)
    
    return render(request, 'users/partials/post_list.html', {
        'posts': posts,
        'profile_user': user
    })


@login_required
def user_comments(request, username):
    """
    Все комментарии пользователя (для HTMX подгрузки).
    """
    user = get_object_or_404(User, username=username)
    comments = user.comments.filter(is_deleted=False).select_related('post__community').order_by('-created_at')
    
    if request.user.is_authenticated:
        for comment in comments:
            comment.user_vote = comment.get_user_vote(request.user)
    
    return render(request, 'users/partials/comment_list.html', {
        'comments': comments,
        'profile_user': user
    })
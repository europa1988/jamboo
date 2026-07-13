from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.http import HttpResponseForbidden, HttpResponse
from django.template.loader import render_to_string

from .models import Community, CommunityMember, CommunityRule
from apps.posts.models import Post


class CommunityListView(ListView):
    """
    Список всех сообществ.
    """
    model = Community
    template_name = 'communities/list.html'
    context_object_name = 'communities'
    paginate_by = 20
    
    def get_queryset(self):
        return Community.objects.all().order_by('-member_count')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Для каждого сообщества проверяем, участвует ли текущий пользователь
        if self.request.user.is_authenticated:
            for community in context['communities']:
                community.is_member = CommunityMember.objects.filter(
                    user=self.request.user,
                    community=community
                ).exists()
        return context


class CommunityDetailView(DetailView):
    """
    Страница сообщества с постами.
    """
    model = Community
    template_name = 'communities/detail.html'
    context_object_name = 'community'
    slug_url_kwarg = 'slug'
    slug_field = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        community = self.object
        
        # Посты сообщества
        context['posts'] = Post.objects.filter(
            community=community,
            is_deleted=False
        ).select_related('author').prefetch_related('votes').order_by('-created_at')[:50]
        
        # Добавляем user_vote к постам
        if self.request.user.is_authenticated:
            for post in context['posts']:
                post.user_vote = post.get_user_vote(self.request.user)
        
        # Проверяем членство
        context['is_member'] = False
        context['user_role'] = None
        if self.request.user.is_authenticated:
            membership = CommunityMember.objects.filter(
                user=self.request.user,
                community=community
            ).first()
            if membership:
                context['is_member'] = True
                context['user_role'] = membership.role
        
        # Правила сообщества
        context['rules'] = community.rules.all()
        
        # Количество модераторов
        context['moderators_count'] = community.members.filter(
            role__in=['moderator', 'admin']
        ).count()
        
        return context


class CommunityCreateView(LoginRequiredMixin, CreateView):
    """
    Создание нового сообщества.
    """
    model = Community
    template_name = 'communities/create.html'
    fields = ['name', 'description', 'community_type', 'avatar', 'banner']
    
    def form_valid(self, form):
        community = form.save(commit=False)
        community.creator = self.request.user
        # Генерируем slug из названия
        from slugify import slugify
        base_slug = slugify(community.name, max_length=50)
        slug = base_slug
        counter = 1
        while Community.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        community.slug = slug
        community.save()
        
        # Автоматически делаем создателя админом
        CommunityMember.objects.create(
            user=self.request.user,
            community=community,
            role='admin'
        )
        community.member_count = 1
        community.save()
        
        messages.success(self.request, f'Сообщество c/{community.name} создано!')
        return redirect('communities:detail', slug=community.slug)


@login_required
def community_join(request, slug):
    """
    Присоединение к сообществу (HTMX).
    """
    community = get_object_or_404(Community, slug=slug)
    
    # Проверяем, не участник ли уже
    if CommunityMember.objects.filter(user=request.user, community=community).exists():
        if request.headers.get('HX-Request'):
            return HttpResponse('Вы уже участник', status=400)
        messages.error(request, 'Вы уже участник этого сообщества.')
        return redirect('communities:detail', slug=slug)
    
    # Присоединяемся
    CommunityMember.objects.create(
        user=request.user,
        community=community,
        role='member'
    )
    
    # Обновляем счётчик
    community.member_count = community.members.count()
    community.save()
    
    # HTMX — возвращаем обновлённую кнопку
    if request.headers.get('HX-Request'):
        html = render_to_string('communities/partials/join_button.html', {
            'community': community,
            'is_member': True,
            'user_role': 'member'
        }, request=request)
        return HttpResponse(html)
    
    messages.success(request, f'Вы присоединились к c/{community.name}!')
    return redirect('communities:detail', slug=slug)


@login_required
def community_leave(request, slug):
    """
    Выход из сообщества (HTMX).
    """
    community = get_object_or_404(Community, slug=slug)
    
    membership = CommunityMember.objects.filter(
        user=request.user,
        community=community
    ).first()
    
    if not membership:
        if request.headers.get('HX-Request'):
            return HttpResponse('Вы не участник', status=400)
        messages.error(request, 'Вы не участник этого сообщества.')
        return redirect('communities:detail', slug=slug)
    
    # Создатель не может выйти (только удалить сообщество)
    if membership.role == 'admin' and community.creator == request.user:
        if request.headers.get('HX-Request'):
            return HttpResponse('Создатель не может выйти', status=400)
        messages.error(request, 'Создатель не может выйти из сообщества.')
        return redirect('communities:detail', slug=slug)
    
    membership.delete()
    
    # Обновляем счётчик
    community.member_count = community.members.count()
    community.save()
    
    # HTMX — возвращаем обновлённую кнопку
    if request.headers.get('HX-Request'):
        html = render_to_string('communities/partials/join_button.html', {
            'community': community,
            'is_member': False,
            'user_role': None
        }, request=request)
        return HttpResponse(html)
    
    messages.success(request, f'Вы покинули c/{community.name}.')
    return redirect('communities:detail', slug=slug)


@login_required
def community_members(request, slug):
    """
    Список участников сообщества.
    """
    community = get_object_or_404(Community, slug=slug)
    members = community.members.select_related('user').order_by('-role', 'joined_at')
    
    return render(request, 'communities/members.html', {
        'community': community,
        'members': members
    })
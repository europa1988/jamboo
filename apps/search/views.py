from django.shortcuts import render
from django.urls import reverse
from django.db.models import Q, Prefetch
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote
from apps.users.models import UserFollow

User = get_user_model()


def search_results(request):
    """
    Полностраничный поиск результатов.
    Возвращает посты, сообщества или пользователей.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts').strip()
    
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    if not query:
        return render(request, 'search/results.html', {
            'query': query,
            'search_type': search_type,
            'results': None,
            'total_count': 0,
        })

    if len(query) < 2:
        return render(request, 'search/results.html', {
            'query': query,
            'search_type': search_type,
            'error': 'Введите поисковый запрос (минимум 2 символа)',
        })

    if search_type == 'posts':
        # Поиск постов (название или текст)
        # Prefetch PostVote для текущего пользователя для оптимизации производительности
        if request.user.is_authenticated:
            queryset = Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                is_deleted=False
            ).select_related('author', 'community').prefetch_related(
                Prefetch('votes', queryset=PostVote.objects.filter(user=request.user), to_attr='user_votes')
            ).order_by('-created_at')
        else:
            queryset = Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                is_deleted=False
            ).select_related('author', 'community').order_by('-created_at')

    elif search_type == 'communities':
        # Поиск по сообществам
        queryset = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        ).order_by('-member_count')

    else:  # 'users'
        # Поиск пользователей
        queryset = User.objects.filter(
            Q(username__icontains=query)
        ).select_related('profile').order_by('username')

    # Пагинация по 10 результатов на страницу
    paginator = Paginator(queryset, 10)
    page = request.GET.get('page')
    try:
        results = paginator.page(page)
    except PageNotAnInteger:
        results = paginator.page(1)
    except EmptyPage:
        results = paginator.page(paginator.num_pages)

    # Доп. логика для постов: проставить user_vote
    if search_type == 'posts' and request.user.is_authenticated:
        for post in results:
            post.user_vote = post.user_votes[0].value if post.user_votes else None

    # Доп. логика для пользователей: проставить is_following
    elif search_type == 'users':
        if request.user.is_authenticated:
            following_ids = set(UserFollow.objects.filter(follower=request.user).values_list('following_id', flat=True))
            for profile_user in results:
                profile_user.is_following = profile_user.id in following_ids
        else:
            for profile_user in results:
                profile_user.is_following = False

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': paginator.count,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX-эндпоинт для автодополнения (поисковые подсказки).
    """
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if len(query) >= 2:
        # 1. Посты
        posts = Post.objects.filter(
            Q(title__icontains=query),
            is_deleted=False
        ).select_related('community', 'author')[:5]
        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f"c/{post.community.name} • u/{post.author.username}",
            })

        # 2. Сообщества
        communities = Community.objects.filter(
            Q(name__icontains=query),
            is_active=True
        )[:3]
        for comm in communities:
            suggestions.append({
                'url': reverse('communities:detail', kwargs={'slug': comm.slug}),
                'type': 'community',
                'title': f"c/{comm.name}",
                'subtitle': comm.description[:100] if comm.description else '',
            })

        # 3. Пользователи
        users = User.objects.filter(
            Q(username__icontains=query)
        ).select_related('profile').order_by('username')[:3]
        for u in users:
            bio = u.profile.bio if hasattr(u, 'profile') and u.profile.bio else ''
            suggestions.append({
                'url': reverse('users:profile', kwargs={'username': u.username}),
                'type': 'user',
                'title': f"u/{u.username}",
                'subtitle': bio[:100] if bio else f"Карма: {u.karma}",
            })

    context = {
        'suggestions': suggestions,
        'query': query,
    }
    return render(request, 'search/partials/suggestions.html', context)

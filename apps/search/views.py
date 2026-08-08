from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote
from apps.users.models import UserFollow

User = get_user_model()


def search_results(request):
    """
    Полностраничный поиск с пагинацией.
    Поддерживает поиск по постам (по умолчанию), сообществам и пользователям.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts').strip()
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    context = {
        'query': query,
        'search_type': search_type,
        'error': None,
        'results': None,
        'total_count': 0,
    }

    if not query:
        context['error'] = 'Введите поисковый запрос'
        return render(request, 'search/results.html', context)

    if len(query) < 2:
        context['error'] = 'Поисковый запрос должен содержать не менее 2 символов'
        return render(request, 'search/results.html', context)

    page_number = request.GET.get('page', 1)

    if search_type == 'posts':
        posts_qs = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            is_deleted=False
        ).select_related('author', 'community').order_by('-created_at')

        if request.user.is_authenticated:
            posts_qs = posts_qs.prefetch_related(
                Prefetch('votes', queryset=PostVote.objects.filter(user=request.user), to_attr='user_votes')
            )

        paginator = Paginator(posts_qs, 10)
        results = paginator.get_page(page_number)

        if request.user.is_authenticated:
            for post in results:
                post.user_vote = post.user_votes[0].value if hasattr(post, 'user_votes') and post.user_votes else None

    elif search_type == 'communities':
        communities_qs = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        ).order_by('-member_count')

        paginator = Paginator(communities_qs, 10)
        results = paginator.get_page(page_number)

    elif search_type == 'users':
        users_qs = User.objects.filter(
            username__icontains=query,
            is_active=True
        ).select_related('profile').order_by('username')

        paginator = Paginator(users_qs, 10)
        results = paginator.get_page(page_number)

        if request.user.is_authenticated:
            following_ids = set(
                UserFollow.objects.filter(
                    follower=request.user,
                    following__in=results.object_list
                ).values_list('following_id', flat=True)
            )
            for profile_user in results:
                profile_user.is_following = profile_user.id in following_ids
        else:
            for profile_user in results:
                profile_user.is_following = False

    context['results'] = results
    context['total_count'] = paginator.count
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX-эндпоинт для автодополнения (suggestions).
    Ожидает контекст со списком 'suggestions' (посты, сообщества, пользователи).
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # 1. Посты (до 5 штук)
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community')[:5]

        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}'
            })

        # 2. Сообщества (до 3 штук)
        communities = Community.objects.filter(
            name__icontains=query,
            is_active=True
        )[:3]

        for community in communities:
            suggestions.append({
                'url': reverse('communities:detail', kwargs={'slug': community.slug}),
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников'
            })

        # 3. Пользователи (до 3 штук)
        users = User.objects.filter(
            username__icontains=query,
            is_active=True
        )[:3]

        for user in users:
            suggestions.append({
                'url': reverse('users:profile', kwargs={'username': user.username}),
                'type': 'user',
                'title': f'u/{user.username}',
                'subtitle': f'Карма: {user.karma}'
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query
    })

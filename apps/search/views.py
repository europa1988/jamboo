from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse

from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow


def search_results(request):
    """
    Полная страница результатов поиска с пагинацией (10 результатов на страницу).
    Поддерживаются типы поиска: posts, communities, users.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts').strip()
    page_number = request.GET.get('page', 1)

    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    error = None
    results = None
    total_count = 0

    if not query:
        error = 'Введите поисковый запрос.'
    else:
        if search_type == 'posts':
            queryset = Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                is_deleted=False
            ).select_related('author', 'community').order_by('-created_at')

            paginator = Paginator(queryset, 10)
            results = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                for post in results:
                    post.user_vote = post.get_user_vote(request.user)

        elif search_type == 'communities':
            queryset = Community.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            ).order_by('-member_count', 'name')

            paginator = Paginator(queryset, 10)
            results = paginator.get_page(page_number)
            total_count = paginator.count

        elif search_type == 'users':
            queryset = User.objects.filter(
                Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query),
                is_active=True
            ).select_related('profile').order_by('username')

            paginator = Paginator(queryset, 10)
            results = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                for profile_user in results:
                    profile_user.is_following = UserFollow.objects.filter(
                        follower=request.user,
                        following=profile_user
                    ).exists()

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
        'error': error,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX эндпоинт автокомплита подсказок поиска.
    Возвращает список подсказок с ключами: url, type, title, subtitle.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # Посты
        posts = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            is_deleted=False
        ).select_related('community').order_by('-created_at')[:3]

        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}',
            })

        # Сообщества
        communities = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).order_by('-member_count', 'name')[:3]

        for community in communities:
            suggestions.append({
                'url': reverse('communities:detail', kwargs={'slug': community.slug}),
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
            })

        # Пользователи
        users = User.objects.filter(
            username__icontains=query,
            is_active=True
        ).order_by('username')[:3]

        for profile_user in users:
            suggestions.append({
                'url': reverse('users:profile', kwargs={'username': profile_user.username}),
                'type': 'user',
                'title': f'u/{profile_user.username}',
                'subtitle': f'Карма: {profile_user.karma}',
            })

    context = {
        'suggestions': suggestions,
        'query': query,
    }
    return render(request, 'search/partials/suggestions.html', context)

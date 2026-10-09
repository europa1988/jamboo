from django.shortcuts import render
from django.core.paginator import Paginator
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow


def search_results(request):
    """Страница результатов поиска."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'
    page = request.GET.get('page', 1)

    if not query or len(query) < 2:
        error = 'Запрос должен содержать минимум 2 символа.' if query else 'Введите поисковый запрос.'
        return render(request, 'search/results.html', {
            'query': query,
            'search_type': search_type,
            'error': error,
            'results': None,
            'total_count': 0,
        })

    total_count = 0
    results = None

    if search_type == 'posts':
        queryset = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('author', 'community').prefetch_related('votes').order_by('-created_at')
        total_count = queryset.count()
        paginator = Paginator(queryset, 10)
        results = paginator.get_page(page)

        if request.user.is_authenticated:
            for post in results.object_list:
                post.user_vote = post.get_user_vote(request.user)

    elif search_type == 'communities':
        queryset = Community.objects.filter(
            name__icontains=query
        ).order_by('-member_count', 'name')
        total_count = queryset.count()
        paginator = Paginator(queryset, 10)
        results = paginator.get_page(page)

    elif search_type == 'users':
        queryset = User.objects.filter(
            username__icontains=query
        ).select_related('profile').order_by('username')
        total_count = queryset.count()
        paginator = Paginator(queryset, 10)
        results = paginator.get_page(page)

        if request.user.is_authenticated:
            following_ids = set(UserFollow.objects.filter(
                follower=request.user,
                following__in=results.object_list
            ).values_list('following_id', flat=True))
            for u in results.object_list:
                u.is_following = u.id in following_ids

    return render(request, 'search/results.html', {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
        'error': None,
    })


def search_suggestions(request):
    """HTMX эндпоинт автокомплита / подсказок поиска."""
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # Посты
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community')[:3]
        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}'
            })

        # Сообщества
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]
        for community in communities:
            suggestions.append({
                'url': community.get_absolute_url(),
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников'
            })

        # Пользователи
        users = User.objects.filter(
            username__icontains=query
        ).order_by('username')[:3]
        for u in users:
            suggestions.append({
                'url': u.get_absolute_url(),
                'type': 'user',
                'title': f'u/{u.username}',
                'subtitle': f'Карма: {u.karma}'
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query
    })

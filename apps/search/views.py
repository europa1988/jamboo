from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow


def search_results(request):
    """
    Основная страница результатов поиска.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page_number = request.GET.get('page', 1)
    results = []
    total_count = 0
    error = None

    if not query:
        return render(request, 'search/results.html', {
            'query': query,
            'search_type': search_type,
            'results': None,
            'total_count': 0,
        })

    if search_type == 'posts':
        queryset = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            is_deleted=False
        ).select_related('author', 'community').prefetch_related('votes').order_by('-created_at')

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
            Q(username__icontains=query) | Q(email__icontains=query) | Q(profile__bio__icontains=query)
        ).distinct().order_by('id')

        paginator = Paginator(queryset, 10)
        results = paginator.get_page(page_number)
        total_count = paginator.count

        if request.user.is_authenticated:
            following_ids = set(
                UserFollow.objects.filter(follower=request.user).values_list('following_id', flat=True)
            )
            for user_obj in results:
                user_obj.is_following = user_obj.id in following_ids

    return render(request, 'search/results.html', {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
        'error': error,
    })


def search_suggestions(request):
    """
    HTMX эндпоинт подсказок поиска.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # Посты (до 3)
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community')[:3]
        for post in posts:
            suggestions.append({
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}' if post.community else '',
                'url': post.get_absolute_url(),
            })

        # Сообщества (до 3)
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]
        for community in communities:
            suggestions.append({
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
                'url': community.get_absolute_url(),
            })

        # Пользователи (до 3)
        users = User.objects.filter(
            username__icontains=query
        ).order_by('id')[:3]
        for u in users:
            suggestions.append({
                'type': 'user',
                'title': f'u/{u.username}',
                'subtitle': f'Карма: {u.karma}',
                'url': u.get_absolute_url(),
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query,
    })

from django.shortcuts import render
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from apps.posts.models import Post
from apps.communities.models import Community

User = get_user_model()


def search_results(request):
    """
    Основное представление результатов поиска (посты, сообщества, пользователи).
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page_number = request.GET.get('page', 1)

    if query:
        if search_type == 'posts':
            queryset = Post.objects.filter(
                title__icontains=query,
                is_deleted=False
            ).select_related('author', 'community').order_by('-created_at')
        elif search_type == 'communities':
            queryset = Community.objects.filter(
                name__icontains=query
            ).order_by('name')
        elif search_type == 'users':
            queryset = User.objects.filter(
                username__icontains=query
            ).select_related('profile').order_by('username')
    else:
        queryset = []

    paginator = Paginator(queryset, 10)
    results = paginator.get_page(page_number)

    if request.user.is_authenticated and query:
        if search_type == 'posts':
            for post in results:
                post.user_vote = post.get_user_vote(request.user)
        elif search_type == 'users':
            following_ids = set(request.user.following.values_list('following_id', flat=True))
            for profile_user in results:
                profile_user.is_following = profile_user.id in following_ids

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': paginator.count if query else 0,
    }

    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX-эндпоинт автодополнения поиска.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community')[:5]

        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}' if post.community else ''
            })

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

        users = User.objects.filter(
            username__icontains=query
        )[:3]

        for u in users:
            suggestions.append({
                'url': u.get_absolute_url(),
                'type': 'user',
                'title': f'u/{u.username}',
                'subtitle': f'Карма: {u.karma}'
            })

    context = {
        'suggestions': suggestions,
        'query': query,
    }

    return render(request, 'search/partials/suggestions.html', context)

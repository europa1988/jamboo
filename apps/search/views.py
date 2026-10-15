from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote

User = get_user_model()


def search_results(request):
    """
    Страница результатов поиска с поддержкой вкладок (посты, сообщества, пользователи) и пагинации.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')

    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    if not query or len(query) < 2:
        return render(request, 'search/results.html', {
            'query': query,
            'search_type': search_type,
            'error': 'Запрос должен содержать минимум 2 символа.'
        })

    page_number = request.GET.get('page', 1)
    results = None
    total_count = 0

    if search_type == 'posts':
        posts_qs = Post.objects.filter(
            is_deleted=False
        ).filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        ).select_related('author', 'community').order_by('-created_at')

        if request.user.is_authenticated:
            posts_qs = posts_qs.prefetch_related(
                Prefetch('votes', queryset=PostVote.objects.filter(user=request.user), to_attr='user_votes')
            )

        paginator = Paginator(posts_qs, 10)
        results = paginator.get_page(page_number)
        total_count = paginator.count

        if request.user.is_authenticated:
            for post in results:
                user_votes = getattr(post, 'user_votes', [])
                post.user_vote = user_votes[0].value if user_votes else None

    elif search_type == 'communities':
        communities_qs = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).order_by('-member_count', 'name')

        paginator = Paginator(communities_qs, 10)
        results = paginator.get_page(page_number)
        total_count = paginator.count

    elif search_type == 'users':
        users_qs = User.objects.filter(
            Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
        ).select_related('profile').order_by('username')

        paginator = Paginator(users_qs, 10)
        results = paginator.get_page(page_number)
        total_count = paginator.count

        if request.user.is_authenticated:
            following_ids = set(request.user.following.values_list('following_id', flat=True))
            for u in results:
                u.is_following = u.id in following_ids
        else:
            for u in results:
                u.is_following = False

    return render(request, 'search/results.html', {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
    })


def search_suggestions(request):
    """
    HTMX эндпоинт для выпадающих подсказок автокомплита.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        posts = Post.objects.filter(
            is_deleted=False
        ).filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        ).select_related('community')[:3]

        for post in posts:
            suggestions.append({
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}' if post.community else 'Пост',
                'url': post.get_absolute_url()
            })

        communities = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )[:3]

        for community in communities:
            suggestions.append({
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
                'url': community.get_absolute_url()
            })

        users = User.objects.filter(
            Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
        )[:3]

        for u in users:
            suggestions.append({
                'type': 'user',
                'title': f'u/{u.username}',
                'subtitle': f'Карма: {u.karma}',
                'url': u.get_absolute_url()
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query
    })

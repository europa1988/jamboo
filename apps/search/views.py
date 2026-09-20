from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User
from apps.votes.models import PostVote


def search_results(request):
    """
    Основной view поиска с пагинацией и оптимизацией запросов.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    page_number = request.GET.get('page', 1)

    if not query:
        return render(request, 'search/results.html', {
            'query': '',
            'search_type': search_type,
            'page_obj': None,
            'total_count': 0,
        })

    items = []
    if search_type == 'posts':
        qs = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('author', 'community')
        if request.user.is_authenticated:
            qs = qs.prefetch_related(
                Prefetch(
                    'votes',
                    queryset=PostVote.objects.filter(user=request.user)
                )
            )
        qs = qs.order_by('-created_at')
        items = qs
    elif search_type == 'communities':
        items = Community.objects.filter(
            name__icontains=query,
            is_active=True
        ).order_by('-member_count')
    elif search_type == 'users':
        items = User.objects.filter(
            username__icontains=query
        ).order_by('username')

    paginator = Paginator(items, 10)
    page_obj = paginator.get_page(page_number)

    if search_type == 'posts' and request.user.is_authenticated:
        for post in page_obj:
            post.user_vote = post.get_user_vote(request.user)

    return render(request, 'search/results.html', {
        'query': query,
        'search_type': search_type,
        'page_obj': page_obj,
        'total_count': paginator.count,
    })


def search_suggestions(request):
    """
    HTMX эндпоинт для автодополнения поиска.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community')[:3]
        for post in posts:
            suggestions.append({
                'title': post.title,
                'subtitle': f"в c/{post.community.name}",
                'type': 'post',
                'url': post.get_absolute_url(),
            })

        communities = Community.objects.filter(
            name__icontains=query,
            is_active=True
        )[:3]
        for community in communities:
            suggestions.append({
                'title': f"c/{community.name}",
                'subtitle': f"{community.member_count} участников",
                'type': 'community',
                'url': community.get_absolute_url(),
            })

        users = User.objects.filter(
            username__icontains=query
        )[:3]
        for user in users:
            suggestions.append({
                'title': f"u/{user.username}",
                'subtitle': "Пользователь",
                'type': 'user',
                'url': user.get_absolute_url(),
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query,
    })

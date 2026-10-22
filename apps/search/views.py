from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User
from apps.votes.models import PostVote


def search_results(request):
    """Страница результатов поиска."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    results = []
    total_count = 0
    error = None

    if not query:
        error = 'Введите поисковый запрос'
    elif len(query) < 2:
        error = 'Запрос должен содержать минимум 2 символа'
    else:
        if search_type == 'posts':
            queryset = Post.objects.filter(
                title__icontains=query,
                is_deleted=False
            ).select_related('author', 'community').order_by('-created_at')

            if request.user.is_authenticated:
                queryset = queryset.prefetch_related(
                    Prefetch(
                        'votes',
                        queryset=PostVote.objects.filter(user=request.user),
                        to_attr='user_vote'
                    )
                )
        elif search_type == 'communities':
            queryset = Community.objects.filter(
                name__icontains=query
            ).order_by('-member_count')
        elif search_type == 'users':
            queryset = User.objects.filter(
                username__icontains=query
            ).order_by('username')

        paginator = Paginator(queryset, 10)
        page_number = request.GET.get('page')
        results = paginator.get_page(page_number)
        total_count = paginator.count

        if request.user.is_authenticated and search_type == 'posts':
            for post in results:
                post.user_vote = post.user_vote[0].value if post.user_vote else 0

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
        'error': error,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """HTMX эндпоинт подсказок поиска."""
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if len(query) >= 2:
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community')[:3]
        
        for p in posts:
            suggestions.append({
                'title': p.title,
                'subtitle': f"в c/{p.community.slug}" if p.community else "Пост",
                'url': p.get_absolute_url(),
                'type': 'post'
            })

        communities = Community.objects.filter(
            name__icontains=query
        )[:3]
        
        for c in communities:
            suggestions.append({
                'title': f"c/{c.name}",
                'subtitle': f"{c.member_count} участников",
                'url': c.get_absolute_url(),
                'type': 'community'
            })

        users = User.objects.filter(
            username__icontains=query
        )[:3]

        for u in users:
            suggestions.append({
                'title': f"u/{u.username}",
                'subtitle': "Пользователь",
                'url': u.get_absolute_url(),
                'type': 'user'
            })

    context = {
        'suggestions': suggestions[:6],
        'query': query
    }
    return render(request, 'search/partials/suggestions.html', context)

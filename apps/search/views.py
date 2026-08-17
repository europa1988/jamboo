from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.contrib.auth import get_user_model
from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote

User = get_user_model()


def search_results(request):
    """Страница результатов поиска (посты, сообщества, пользователи)."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    page_number = request.GET.get('page', 1)

    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    error = None
    page_obj = None
    total_count = 0

    if not query:
        error = 'Введите поисковый запрос.'
    elif len(query) < 2:
        error = 'Поисковый запрос должен содержать минимум 2 символа.'
    else:
        if search_type == 'posts':
            queryset = Post.objects.filter(
                title__icontains=query,
                is_deleted=False
            ).select_related('author', 'community').order_by('-created_at')

            if request.user.is_authenticated:
                user_votes = PostVote.objects.filter(user=request.user)
                queryset = queryset.prefetch_related(
                    Prefetch('votes', queryset=user_votes, to_attr='current_user_votes')
                )

        elif search_type == 'communities':
            queryset = Community.objects.filter(
                name__icontains=query,
                is_active=True
            ).order_by('-created_at')

        elif search_type == 'users':
            queryset = User.objects.filter(
                username__icontains=query
            ).order_by('username')

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)
        total_count = paginator.count

    context = {
        'query': query,
        'search_type': search_type,
        'page_obj': page_obj,
        'total_count': total_count,
        'error': error,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """HTMX автокомплит для поиска."""
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # Посты
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community')[:3]
        for p in posts:
            suggestions.append({
                'title': p.title,
                'subtitle': f"в r/{p.community.slug}" if p.community else f"от u/{p.author.username}",
                'type': 'post',
                'url': p.get_absolute_url() if hasattr(p, 'get_absolute_url') else f"/posts/{p.id}/"
            })

        # Сообщества
        communities = Community.objects.filter(
            name__icontains=query,
            is_active=True
        )[:3]
        for c in communities:
            suggestions.append({
                'title': c.name,
                'subtitle': f"r/{c.slug}",
                'type': 'community',
                'url': c.get_absolute_url() if hasattr(c, 'get_absolute_url') else f"/r/{c.slug}/"
            })

        # Пользователи
        users = User.objects.filter(
            username__icontains=query
        ).order_by('username')[:3]
        for u in users:
            suggestions.append({
                'title': u.username,
                'subtitle': f"u/{u.username}",
                'type': 'user',
                'url': u.get_absolute_url() if hasattr(u, 'get_absolute_url') else f"/u/{u.username}/"
            })

    context = {
        'suggestions': suggestions,
        'query': query,
    }
    return render(request, 'search/partials/suggestions.html', context)

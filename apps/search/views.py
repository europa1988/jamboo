from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User
from apps.votes.models import PostVote


def search_results(request):
    """Страница результатов поиска с пагинацией."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page_number = request.GET.get('page', 1)
    results = []
    total_count = 0
    error = None

    if query:
        if len(query) < 2:
            error = "Минимальная длина запроса — 2 символа."
        else:
            if search_type == 'posts':
                queryset = Post.objects.filter(
                    title__icontains=query,
                    is_deleted=False
                ).select_related('author', 'community')
                if request.user.is_authenticated:
                    queryset = queryset.prefetch_related(
                        Prefetch('votes', queryset=PostVote.objects.filter(user=request.user), to_attr='user_vote')
                    )
            elif search_type == 'communities':
                queryset = Community.objects.filter(
                    name__icontains=query
                ).order_by('name')
            elif search_type == 'users':
                queryset = User.objects.filter(
                    username__icontains=query
                ).order_by('username')

            paginator = Paginator(queryset, 10)
            page_obj = paginator.get_page(page_number)
            results = page_obj
            total_count = paginator.count

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'page_obj': results,
        'total_count': total_count,
        'error': error,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """HTMX эндпоинт автокомплита поиска."""
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
                'type': 'post',
                'title': post.title,
                'subtitle': f"в c/{post.community.slug}" if post.community else "",
                'url': post.get_absolute_url() if hasattr(post, 'get_absolute_url') else f"/posts/{post.slug}/"
            })

        # Сообщества
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]
        for community in communities:
            suggestions.append({
                'type': 'community',
                'title': community.name,
                'subtitle': f"{community.member_count} участников" if hasattr(community, 'member_count') else "",
                'url': community.get_absolute_url() if hasattr(community, 'get_absolute_url') else f"/c/{community.slug}/"
            })

        # Пользователи
        users = User.objects.filter(
            username__icontains=query
        ).order_by('username')[:3]
        for u in users:
            suggestions.append({
                'type': 'user',
                'title': u.username,
                'subtitle': f"@{u.username}",
                'url': u.get_absolute_url() if hasattr(u, 'get_absolute_url') else f"/u/{u.username}/"
            })

    context = {
        'suggestions': suggestions,
        'query': query
    }
    return render(request, 'search/partials/suggestions.html', context)

from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote

User = get_user_model()


def search_results(request):
    """Основные результаты поиска с пагинацией (10 элементов на страницу)."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    page_number = request.GET.get('page', 1)

    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    results = []
    total_count = 0
    error = None

    if not query:
        error = "Введите поисковый запрос"
    else:
        if search_type == 'posts':
            posts_qs = Post.objects.filter(
                title__icontains=query,
                is_deleted=False
            ).select_related('community', 'author').order_by('-created_at')

            paginator = Paginator(posts_qs, 10)
            results = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                user_votes = PostVote.objects.filter(user=request.user, post__in=results.object_list)
                vote_dict = {v.post_id: v.value for v in user_votes}
                for post in results.object_list:
                    post.user_vote = vote_dict.get(post.id, 0)
            else:
                for post in results.object_list:
                    post.user_vote = 0

        elif search_type == 'communities':
            communities_qs = Community.objects.filter(
                name__icontains=query,
                is_active=True
            ).order_by('-member_count', 'name')

            paginator = Paginator(communities_qs, 10)
            results = paginator.get_page(page_number)
            total_count = paginator.count

        elif search_type == 'users':
            users_qs = User.objects.filter(
                username__icontains=query,
                is_active=True
            ).select_related('profile').order_by('username')

            paginator = Paginator(users_qs, 10)
            results = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                following_ids = set(request.user.following.values_list('followed_id', flat=True))
                for u in results.object_list:
                    u.is_following = u.id in following_ids

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
        'error': error,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """HTMX эндпоинт для автодополнения (suggestions)."""
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
                'url': p.get_absolute_url(),
                'type': 'post',
                'title': p.title,
                'subtitle': f"c/{p.community.name}"
            })

        # Сообщества
        communities = Community.objects.filter(
            name__icontains=query,
            is_active=True
        )[:3]
        for c in communities:
            suggestions.append({
                'url': c.get_absolute_url(),
                'type': 'community',
                'title': f"c/{c.name}",
                'subtitle': f"{c.member_count} участников"
            })

        # Пользователи
        users = User.objects.filter(
            username__icontains=query,
            is_active=True
        )[:3]
        for u in users:
            suggestions.append({
                'url': u.get_absolute_url(),
                'type': 'user',
                'title': f"u/{u.username}",
                'subtitle': f"Карма: {u.karma}"
            })

    context = {
        'suggestions': suggestions,
        'query': query
    }
    return render(request, 'search/partials/suggestions.html', context)

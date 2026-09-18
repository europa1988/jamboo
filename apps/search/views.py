from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User
from apps.votes.models import PostVote


def search_results(request):
    """Страница результатов поиска (посты, сообщества, пользователи)."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page_number = request.GET.get('page', 1)
    results = []
    total_count = 0
    error = None

    if not query:
        error = 'Введите поисковый запрос.'
    else:
        if search_type == 'posts':
            qs = Post.objects.filter(
                is_deleted=False,
                title__icontains=query
            ).select_related('author', 'community').order_by('-created_at')
            paginator = Paginator(qs, 10)
            page_obj = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                for post in page_obj.object_list:
                    post.user_vote = post.get_user_vote(request.user)

            results = page_obj

        elif search_type == 'communities':
            qs = Community.objects.filter(
                name__icontains=query
            ).order_by('-member_count', 'name')
            paginator = Paginator(qs, 10)
            page_obj = paginator.get_page(page_number)
            total_count = paginator.count
            results = page_obj

        elif search_type == 'users':
            qs = User.objects.filter(
                username__icontains=query
            ).select_related('profile').order_by('username')
            paginator = Paginator(qs, 10)
            page_obj = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                # Assuming user profile follow relationships or similar
                from apps.users.models import UserFollow
                following_ids = set(
                    UserFollow.objects.filter(follower=request.user).values_list('following_id', flat=True)
                )
                for u in page_obj.object_list:
                    u.is_following = u.id in following_ids

            results = page_obj

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
        'error': error,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """HTMX эндпоинт автокомплита поиска."""
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
                'title': post.title,
                'subtitle': f'c/{post.community.name}' if post.community else '',
                'url': post.get_absolute_url(),
                'type': 'post',
            })

        # Сообщества (до 3)
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]
        for community in communities:
            suggestions.append({
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
                'url': community.get_absolute_url(),
                'type': 'community',
            })

        # Пользователи (до 3)
        users = User.objects.filter(
            username__icontains=query
        )[:3]
        for u in users:
            suggestions.append({
                'title': f'u/{u.username}',
                'subtitle': f'Карма: {u.karma}',
                'url': u.get_absolute_url(),
                'type': 'user',
            })

    context = {
        'suggestions': suggestions,
        'query': query,
    }
    return render(request, 'search/partials/suggestions.html', context)

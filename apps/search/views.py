from django.shortcuts import render
from django.core.paginator import Paginator
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_results(request):
    """
    Основной поиск с пагинацией (посты, сообщества, пользователи).
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    page_number = request.GET.get('page', 1)

    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    context = {
        'query': query,
        'search_type': search_type,
        'results': [],
        'total_count': 0,
        'error': None
    }

    if not query:
        context['error'] = 'Введите поисковый запрос'
        return render(request, 'search/results.html', context)

    if search_type == 'posts':
        queryset = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('author', 'community').order_by('-created_at')

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)

        if request.user.is_authenticated:
            page_posts = list(page_obj.object_list)
            page_post_ids = [p.id for p in page_posts]
            user_votes = {
                vote.post_id: vote.value
                for vote in PostVote.objects.filter(user=request.user, post_id__in=page_post_ids)
            }
            for post in page_posts:
                post.user_vote = user_votes.get(post.id)
            page_obj.object_list = page_posts

        context['results'] = page_obj
        context['total_count'] = paginator.count

    elif search_type == 'communities':
        queryset = Community.objects.filter(
            name__icontains=query
        ).order_by('-member_count')

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)

        context['results'] = page_obj
        context['total_count'] = paginator.count

    elif search_type == 'users':
        queryset = User.objects.filter(
            username__icontains=query
        ).select_related('profile').order_by('username')

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)

        if request.user.is_authenticated:
            page_users = list(page_obj.object_list)
            user_ids = [u.id for u in page_users]
            following_ids = set(
                UserFollow.objects.filter(
                    follower=request.user,
                    following_id__in=user_ids
                ).values_list('following_id', flat=True)
            )
            for profile_user in page_users:
                profile_user.is_following = profile_user.id in following_ids
            page_obj.object_list = page_users

        context['results'] = page_obj
        context['total_count'] = paginator.count

    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX эндпоинт автокомплита поиска.
    """
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
                'subtitle': f"c/{post.community.name}",
            })

        # Сообщества
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]
        for community in communities:
            suggestions.append({
                'url': community.get_absolute_url(),
                'type': 'community',
                'title': f"c/{community.name}",
                'subtitle': f"{community.member_count} участников",
            })

        # Пользователи
        users = User.objects.filter(
            username__icontains=query
        ).order_by('username')[:3]
        for profile_user in users:
            suggestions.append({
                'url': profile_user.get_absolute_url(),
                'type': 'user',
                'title': f"u/{profile_user.username}",
                'subtitle': f"Карма: {profile_user.karma}",
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query
    })


def autocomplete(request):
    """Алиас для search_suggestions для обратной совместимости."""
    return search_suggestions(request)

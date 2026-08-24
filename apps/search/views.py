from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch, Exists, OuterRef, Value
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_results(request):
    """
    Основное представление результатов поиска с пагинацией (10 на страницу).
    Поддерживает поиск по постам, сообществам и пользователям.
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
        return render(request, 'search/results.html', context)

    if search_type == 'posts':
        queryset = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community', 'author').order_by('-created_at')

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)

        # Prefetch user votes for posts on current page
        if request.user.is_authenticated:
            user_votes = PostVote.objects.filter(user=request.user)
            post_ids = [p.id for p in page_obj.object_list]
            votes_map = {v.post_id: v for v in user_votes.filter(post_id__in=post_ids)}
            for post in page_obj.object_list:
                post.user_vote = votes_map.get(post.id)

        context['results'] = page_obj
        context['total_count'] = paginator.count

    elif search_type == 'communities':
        queryset = Community.objects.filter(
            name__icontains=query,
            is_active=True
        ).order_by('-member_count', 'name')

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)

        context['results'] = page_obj
        context['total_count'] = paginator.count

    elif search_type == 'users':
        queryset = User.objects.filter(
            username__icontains=query,
            is_active=True
        ).select_related('profile').order_by('username')

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)

        if request.user.is_authenticated:
            following_ids = set(
                UserFollow.objects.filter(
                    follower=request.user,
                    following_id__in=[u.id for u in page_obj.object_list]
                ).values_list('following_id', flat=True)
            )
            for user_obj in page_obj.object_list:
                user_obj.is_following = user_obj.id in following_ids

        context['results'] = page_obj
        context['total_count'] = paginator.count

    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX эндпоинт для автодополнения поиска (подсказок).
    Возвращает список словарей 'suggestions' с атрибутами url, type, title, subtitle.
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
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}' if post.community else 'Пост'
            })

        communities = Community.objects.filter(
            name__icontains=query,
            is_active=True
        )[:3]

        for comm in communities:
            suggestions.append({
                'url': comm.get_absolute_url(),
                'type': 'community',
                'title': f'c/{comm.name}',
                'subtitle': f'{comm.member_count} участников'
            })

        users = User.objects.filter(
            username__icontains=query,
            is_active=True
        )[:3]

        for u in users:
            suggestions.append({
                'url': u.get_absolute_url(),
                'type': 'user',
                'title': f'u/{u.username}',
                'subtitle': f'Карма: {u.karma}'
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query
    })

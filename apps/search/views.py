from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_results(request):
    """
    Основное представление результатов поиска с пагинацией.
    Поддерживает поиск по постам, сообществам и пользователям.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    page_number = request.GET.get('page', 1)

    if not query:
        return render(request, 'search/results.html', {
            'query': '',
            'search_type': search_type,
            'results': None,
            'total_count': 0,
            'error': 'Введите поисковый запрос.'
        })

    results = []
    total_count = 0

    if search_type == 'posts':
        qs = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            is_deleted=False
        ).select_related('author', 'community')

        if request.user.is_authenticated:
            qs = qs.prefetch_related(
                Prefetch(
                    'votes',
                    queryset=PostVote.objects.filter(user=request.user),
                    to_attr='user_votes'
                )
            )

        qs = qs.order_by('-created_at')
        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(page_number)

        if request.user.is_authenticated:
            for post in page_obj:
                votes = getattr(post, 'user_votes', [])
                post.user_vote = votes[0].value if votes else None
        else:
            for post in page_obj:
                post.user_vote = None

        results = page_obj
        total_count = paginator.count

    elif search_type == 'communities':
        qs = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).order_by('-member_count')

        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(page_number)
        results = page_obj
        total_count = paginator.count

    elif search_type == 'users':
        qs = User.objects.filter(
            Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
        ).select_related('profile').order_by('-karma', 'username')

        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(page_number)

        if request.user.is_authenticated:
            following_ids = set(
                UserFollow.objects.filter(
                    follower=request.user,
                    following__in=[u.id for u in page_obj]
                ).values_list('following_id', flat=True)
            )
            for profile_user in page_obj:
                profile_user.is_following = profile_user.id in following_ids
        else:
            for profile_user in page_obj:
                profile_user.is_following = False

        results = page_obj
        total_count = paginator.count

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX эндпоинт автокомплита / подсказок поиска.
    Возвращает список подсказок (посты, сообщества, пользователи).
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
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}',
                'url': post.get_absolute_url()
            })

        communities = Community.objects.filter(
            name__icontains=query
        )[:3]

        for community in communities:
            suggestions.append({
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
                'url': f'/c/{community.slug}/'
            })

        users = User.objects.filter(
            username__icontains=query
        )[:3]

        for u in users:
            suggestions.append({
                'type': 'user',
                'title': f'u/{u.username}',
                'subtitle': f'Карма: {u.karma}',
                'url': f'/u/{u.username}/'
            })

    context = {
        'query': query,
        'suggestions': suggestions
    }
    return render(request, 'search/partials/suggestions.html', context)

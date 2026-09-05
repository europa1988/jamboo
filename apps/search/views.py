from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_results(request):
    """
    Основная страница результатов поиска по постам, сообществам и пользователям.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page = request.GET.get('page', 1)

    if not query:
        return render(request, 'search/results.html', {
            'query': '',
            'search_type': search_type,
            'error': 'Введите поисковый запрос'
        })

    if len(query) < 2:
        return render(request, 'search/results.html', {
            'query': query,
            'search_type': search_type,
            'error': 'Поисковый запрос должен содержать минимум 2 символа.'
        })

    total_count = 0
    results = None

    if search_type == 'posts':
        qs = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            is_deleted=False
        ).select_related('author', 'community').order_by('-created_at')

        if request.user.is_authenticated:
            qs = qs.prefetch_related(
                Prefetch('votes', queryset=PostVote.objects.filter(user=request.user), to_attr='user_votes')
            )

        paginator = Paginator(qs, 10)
        results = paginator.get_page(page)

        if request.user.is_authenticated:
            for post in results:
                post.user_vote = post.get_user_vote(request.user)

        total_count = paginator.count

    elif search_type == 'communities':
        qs = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        ).order_by('-member_count', 'name')

        paginator = Paginator(qs, 10)
        results = paginator.get_page(page)
        total_count = paginator.count

    elif search_type == 'users':
        qs = User.objects.filter(
            Q(username__icontains=query) | Q(profile__bio__icontains=query),
            is_active=True
        ).select_related('profile').order_by('username')

        paginator = Paginator(qs, 10)
        results = paginator.get_page(page)

        if request.user.is_authenticated:
            following_ids = set(
                UserFollow.objects.filter(follower=request.user).values_list('following_id', flat=True)
            )
            for user_obj in results:
                user_obj.is_following = user_obj.id in following_ids

        total_count = paginator.count

    return render(request, 'search/results.html', {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
    })


def search_suggestions(request):
    """
    HTMX эндпоинт автокомплита / подсказок поиска.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # Посты
        posts = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            is_deleted=False
        ).select_related('community')[:3]
        for p in posts:
            suggestions.append({
                'type': 'post',
                'title': p.title,
                'subtitle': f'c/{p.community.name}' if p.community else '',
                'url': p.get_absolute_url()
            })

        # Сообщества
        communities = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        )[:3]
        for c in communities:
            suggestions.append({
                'type': 'community',
                'title': f'c/{c.name}',
                'subtitle': f'{c.member_count} участников',
                'url': c.get_absolute_url()
            })

        # Пользователи
        users = User.objects.filter(
            username__icontains=query,
            is_active=True
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
        'query': query,
    })

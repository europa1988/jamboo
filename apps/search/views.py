from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Prefetch
from django.urls import reverse

from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User
from apps.votes.models import PostVote


def search_results(request):
    """
    Полностраничный поиск с пагинацией (10 результатов на страницу).
    Ищет посты, сообщества или пользователей.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts').strip()
    
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    if not query:
        return render(request, 'search/results.html', {
            'query': '',
            'search_type': search_type,
            'results': None,
            'total_count': 0,
            'error': 'Введите поисковый запрос'
        })

    total_count = 0
    results = None

    if search_type == 'posts':
        posts_qs = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('author', 'community').order_by('-created_at')

        if request.user.is_authenticated:
            posts_qs = posts_qs.prefetch_related(
                Prefetch(
                    'votes',
                    queryset=PostVote.objects.filter(user=request.user),
                    to_attr='current_user_votes'
                )
            )

        total_count = posts_qs.count()

        paginator = Paginator(posts_qs, 10)
        page_number = request.GET.get('page')
        try:
            results = paginator.page(page_number)
        except PageNotAnInteger:
            results = paginator.page(1)
        except EmptyPage:
            results = paginator.page(paginator.num_pages)

        # Установка user_vote после пагинации
        for post in results:
            if request.user.is_authenticated:
                user_votes = getattr(post, 'current_user_votes', [])
                post.user_vote = user_votes[0].value if user_votes else None
            else:
                post.user_vote = None

    elif search_type == 'communities':
        communities_qs = Community.objects.filter(
            name__icontains=query,
            is_active=True
        ).order_by('-member_count')

        total_count = communities_qs.count()

        paginator = Paginator(communities_qs, 10)
        page_number = request.GET.get('page')
        try:
            results = paginator.page(page_number)
        except PageNotAnInteger:
            results = paginator.page(1)
        except EmptyPage:
            results = paginator.page(paginator.num_pages)

    elif search_type == 'users':
        users_qs = User.objects.filter(
            username__icontains=query,
            is_active=True
        ).select_related('profile').order_by('username')

        total_count = users_qs.count()

        paginator = Paginator(users_qs, 10)
        page_number = request.GET.get('page')
        try:
            results = paginator.page(page_number)
        except PageNotAnInteger:
            results = paginator.page(1)
        except EmptyPage:
            results = paginator.page(paginator.num_pages)

        # Установка is_following после пагинации
        if request.user.is_authenticated:
            from apps.users.models import UserFollow
            user_ids = [u.id for u in results]
            following_ids = set(
                UserFollow.objects.filter(
                    follower=request.user,
                    following_id__in=user_ids
                ).values_list('following_id', flat=True)
            )
            for u in results:
                u.is_following = u.id in following_ids
        else:
            for u in results:
                u.is_following = False

    return render(request, 'search/results.html', {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count
    })


def search_suggestions(request):
    """
    HTMX эндпоинт автокомплита поиска (suggestions).
    Ожидает контекст со списком 'suggestions' из элементов,
    где каждый элемент содержит ключи: 'url', 'type', 'title', 'subtitle'.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if len(query) >= 2:
        # Поиск постов (до 5 штук)
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community', 'author')[:5]
        for p in posts:
            suggestions.append({
                'url': p.get_absolute_url(),
                'type': 'post',
                'title': p.title,
                'subtitle': f"Пост в c/{p.community.name} • u/{p.author.username}"
            })

        # Поиск сообществ (до 3 штук)
        communities = Community.objects.filter(
            name__icontains=query,
            is_active=True
        )[:3]
        for c in communities:
            suggestions.append({
                'url': reverse('communities:detail', kwargs={'slug': c.slug}),
                'type': 'community',
                'title': f"c/{c.name}",
                'subtitle': f"{c.member_count} участников"
            })

        # Поиск пользователей (до 3 штук)
        users = User.objects.filter(
            username__icontains=query,
            is_active=True
        ).order_by('username')[:3]
        for u in users:
            suggestions.append({
                'url': reverse('users:profile', kwargs={'username': u.username}),
                'type': 'user',
                'title': f"u/{u.username}",
                'subtitle': f"Карма: {u.karma}"
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query,
    })

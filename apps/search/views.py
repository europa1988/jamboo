from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
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

    context = {
        'query': query,
        'search_type': search_type,
        'results': None,
        'total_count': 0,
        'error': None
    }

    if not query:
        return render(request, 'search/results.html', context)

    if len(query) < 2:
        context['error'] = 'Поисковый запрос должен содержать минимум 2 символа'
        return render(request, 'search/results.html', context)

    page_number = request.GET.get('page', 1)

    if search_type == 'posts':
        queryset = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            is_deleted=False
        ).select_related('author', 'community')

        if request.user.is_authenticated:
            queryset = queryset.prefetch_related(
                Prefetch(
                    'votes',
                    queryset=PostVote.objects.filter(user=request.user),
                    to_attr='user_votes'
                )
            )

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)

        if request.user.is_authenticated:
            for post in page_obj:
                votes = getattr(post, 'user_votes', [])
                post.user_vote = votes[0] if votes else None

        context['results'] = page_obj
        context['total_count'] = paginator.count

    elif search_type == 'communities':
        queryset = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        ).order_by('-member_count')

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)

        context['results'] = page_obj
        context['total_count'] = paginator.count

    elif search_type == 'users':
        queryset = User.objects.filter(
            Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query),
            is_active=True
        ).select_related('profile').order_by('-karma', 'id')

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)

        if request.user.is_authenticated:
            following_ids = set(
                request.user.following.values_list('followed_id', flat=True)
            )
            for profile_user in page_obj:
                profile_user.is_following = profile_user.id in following_ids

        context['results'] = page_obj
        context['total_count'] = paginator.count

    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """HTMX эндпоинт для выпадающих подсказок поиска."""
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # Посты
        posts = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            is_deleted=False
        ).select_related('community')[:3]

        for post in posts:
            suggestions.append({
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}' if post.community else 'Пост',
                'url': post.get_absolute_url()
            })

        # Сообщества
        communities = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        )[:3]

        for community in communities:
            suggestions.append({
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
                'url': community.get_absolute_url()
            })

        # Пользователи
        users = User.objects.filter(
            Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query),
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
        'query': query
    })

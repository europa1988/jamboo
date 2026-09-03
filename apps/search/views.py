from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User
from apps.votes.models import PostVote


def search_results(request):
    """
    Основное представление результатов поиска по постам, сообществам и пользователям.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    page = request.GET.get('page', 1)

    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    context = {
        'query': query,
        'search_type': search_type,
        'results': [],
        'total_count': 0,
    }

    if not query:
        return render(request, 'search/results.html', context)

    if len(query) < 2:
        context['error'] = 'Поисковый запрос должен быть не менее 2 символов.'
        return render(request, 'search/results.html', context)

    if search_type == 'posts':
        queryset = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community', 'author')

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page)

        if request.user.is_authenticated:
            post_ids = [p.id for p in page_obj.object_list]
            votes = PostVote.objects.filter(user=request.user, post_id__in=post_ids)
            vote_map = {v.post_id: v.value for v in votes}
            for post in page_obj.object_list:
                post.user_vote = vote_map.get(post.id)

        context['results'] = page_obj
        context['total_count'] = paginator.count

    elif search_type == 'communities':
        queryset = Community.objects.filter(
            name__icontains=query,
            is_active=True
        )

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page)

        context['results'] = page_obj
        context['total_count'] = paginator.count

    elif search_type == 'users':
        queryset = User.objects.filter(
            username__icontains=query,
            is_active=True
        ).order_by('username')

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page)

        if request.user.is_authenticated:
            following_ids = set(request.user.following.values_list('followed_id', flat=True))
            for u in page_obj.object_list:
                u.is_following = u.id in following_ids

        context['results'] = page_obj
        context['total_count'] = paginator.count

    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX эндпоинт для автодополнения (подсказок) поиска.
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
                'url': post.get_absolute_url(),
            })

        communities = Community.objects.filter(
            name__icontains=query,
            is_active=True
        )[:3]

        for community in communities:
            suggestions.append({
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
                'url': community.get_absolute_url(),
            })

        users = User.objects.filter(
            username__icontains=query,
            is_active=True
        )[:3]

        for u in users:
            suggestions.append({
                'type': 'user',
                'title': f'u/{u.username}',
                'subtitle': f'Карма: {u.karma}',
                'url': u.get_absolute_url(),
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query,
    })

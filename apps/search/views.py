from django.shortcuts import render
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote
from apps.users.models import UserFollow

User = get_user_model()


def search_results(request):
    """
    Основная страница результатов поиска.
    Поддерживает поиск по постам, сообществам и пользователям.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page_number = request.GET.get('page', 1)

    if not query:
        context = {
            'query': '',
            'search_type': search_type,
            'results': None,
            'total_count': 0,
        }
        return render(request, 'search/results.html', context)

    if search_type == 'posts':
        posts = Post.objects.filter(
            is_deleted=False
        ).filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        ).select_related('author', 'community').order_by('-created_at')

        if request.user.is_authenticated:
            posts = posts.prefetch_related(
                Prefetch('votes', queryset=PostVote.objects.filter(user=request.user))
            )

        paginator = Paginator(posts, 10)
        results = paginator.get_page(page_number)

        if request.user.is_authenticated:
            for post in results:
                post.user_vote = post.get_user_vote(request.user)

    elif search_type == 'communities':
        communities = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).order_by('-member_count')

        paginator = Paginator(communities, 10)
        results = paginator.get_page(page_number)

    else:  # users
        users = User.objects.filter(
            Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
        ).select_related('profile').order_by('id')

        paginator = Paginator(users, 10)
        results = paginator.get_page(page_number)

        if request.user.is_authenticated:
            following_ids = set(
                UserFollow.objects.filter(
                    follower=request.user,
                    following__in=[u.id for u in results]
                ).values_list('following_id', flat=True)
            )
            for profile_user in results:
                profile_user.is_following = profile_user.id in following_ids
        else:
            for profile_user in results:
                profile_user.is_following = False

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': paginator.count,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX эндпоинт выпадающих подсказок поиска (автокомплит).
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community')[:3]

        for p in posts:
            suggestions.append({
                'url': p.get_absolute_url(),
                'type': 'post',
                'title': p.title,
                'subtitle': f'c/{p.community.name}'
            })

        communities = Community.objects.filter(
            name__icontains=query
        )[:3]

        for c in communities:
            suggestions.append({
                'url': c.get_absolute_url(),
                'type': 'community',
                'title': f'c/{c.name}',
                'subtitle': f'{c.member_count} участников'
            })

        users = User.objects.filter(
            username__icontains=query
        ).order_by('id')[:3]

        for u in users:
            suggestions.append({
                'url': u.get_absolute_url(),
                'type': 'user',
                'title': f'u/{u.username}',
                'subtitle': f'Карма: {u.karma}'
            })

    context = {
        'suggestions': suggestions,
        'query': query,
    }
    return render(request, 'search/partials/suggestions.html', context)

from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_results(request):
    """Отображение страницы результатов поиска."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    page_number = request.GET.get('page', 1)

    if not query:
        return render(request, 'search/results.html', {
            'query': '',
            'search_type': search_type,
            'results': None,
            'total_count': 0,
        })

    if search_type == 'communities':
        queryset = Community.objects.filter(name__icontains=query).order_by('-member_count')
        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)
        total_count = paginator.count

    elif search_type == 'users':
        queryset = User.objects.filter(username__icontains=query).select_related('profile').order_by('username')
        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)
        total_count = paginator.count

        if request.user.is_authenticated:
            following_ids = set(
                UserFollow.objects.filter(follower=request.user).values_list('following_id', flat=True)
            )
            for user_obj in page_obj:
                user_obj.is_following = user_obj.id in following_ids

    else:  # default to 'posts'
        search_type = 'posts'
        queryset = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('author', 'community').order_by('-created_at')

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
        total_count = paginator.count

        if request.user.is_authenticated:
            for post in page_obj:
                votes = getattr(post, 'user_votes', [])
                post.user_vote = votes[0].value if votes else None

    context = {
        'query': query,
        'search_type': search_type,
        'results': page_obj,
        'total_count': total_count,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """HTMX эндпоинт автокомплита поиска."""
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community')[:3]

        for post in posts:
            suggestions.append({
                'title': post.title,
                'subtitle': f'c/{post.community.name}',
                'type': 'post',
                'url': post.get_absolute_url(),
            })

        communities = Community.objects.filter(
            name__icontains=query
        )[:3]

        for community in communities:
            suggestions.append({
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
                'type': 'community',
                'url': community.get_absolute_url(),
            })

        users = User.objects.filter(
            username__icontains=query
        ).order_by('username')[:3]

        for user in users:
            suggestions.append({
                'title': f'u/{user.username}',
                'subtitle': f'Карма: {user.karma}',
                'type': 'user',
                'url': user.get_absolute_url(),
            })

    context = {
        'suggestions': suggestions,
        'query': query,
    }
    return render(request, 'search/partials/suggestions.html', context)

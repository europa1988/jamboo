from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_results(request):
    """Отображение результатов поиска по постам, сообществам и пользователям."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    page_number = request.GET.get('page', 1)

    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    results = []
    total_count = 0

    if query:
        if search_type == 'posts':
            posts = Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                is_deleted=False
            ).select_related('community', 'author').order_by('-created_at')

            total_count = posts.count()
            paginator = Paginator(posts, 10)
            page_obj = paginator.get_page(page_number)

            if request.user.is_authenticated:
                user_votes = PostVote.objects.filter(user=request.user, post__in=page_obj.object_list)
                votes_dict = {vote.post_id: vote.value for vote in user_votes}
                for post in page_obj.object_list:
                    post.user_vote = votes_dict.get(post.id, 0)
            else:
                for post in page_obj.object_list:
                    post.user_vote = 0

            results = page_obj

        elif search_type == 'communities':
            communities = Community.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query),
                is_active=True
            ).order_by('name')

            total_count = communities.count()
            paginator = Paginator(communities, 10)
            results = paginator.get_page(page_number)

        elif search_type == 'users':
            users = User.objects.filter(
                username__icontains=query,
                is_active=True
            ).select_related('profile').order_by('username')

            total_count = users.count()
            paginator = Paginator(users, 10)
            page_obj = paginator.get_page(page_number)

            if request.user.is_authenticated:
                following_ids = set(
                    UserFollow.objects.filter(
                        follower=request.user,
                        following__in=page_obj.object_list
                    ).values_list('following_id', flat=True)
                )
                for u in page_obj.object_list:
                    u.is_following = u.id in following_ids
            else:
                for u in page_obj.object_list:
                    u.is_following = False

            results = page_obj

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
    }

    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """HTMX эндпоинт автокомплита поиска."""
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        posts = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            is_deleted=False
        ).select_related('community')[:3]

        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}' if post.community else ''
            })

        communities = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        )[:3]

        for community in communities:
            suggestions.append({
                'url': community.get_absolute_url(),
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников'
            })

        users = User.objects.filter(
            username__icontains=query,
            is_active=True
        )[:3]

        for user_obj in users:
            suggestions.append({
                'url': user_obj.get_absolute_url(),
                'type': 'user',
                'title': f'u/{user_obj.username}',
                'subtitle': f'Карма: {user_obj.karma}'
            })

    context = {
        'query': query,
        'suggestions': suggestions
    }

    return render(request, 'search/partials/suggestions.html', context)

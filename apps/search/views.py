from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch

from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User
from apps.votes.models import PostVote


def search_results(request):
    """Отображение результатов поиска по постам, сообществам и пользователям."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts').strip()
    page = request.GET.get('page', 1)

    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    results = []
    total_count = 0

    if query:
        if search_type == 'posts':
            posts_qs = Post.objects.filter(
                is_deleted=False
            ).filter(
                Q(title__icontains=query) | Q(content__icontains=query)
            ).select_related('author', 'community').order_by('-created_at')

            if request.user.is_authenticated:
                posts_qs = posts_qs.prefetch_related(
                    Prefetch('votes', queryset=PostVote.objects.filter(user=request.user), to_attr='user_votes')
                )

            paginator = Paginator(posts_qs, 10)
            results = paginator.get_page(page)
            total_count = paginator.count

            if request.user.is_authenticated:
                for post in results:
                    if hasattr(post, 'user_votes') and post.user_votes:
                        post.user_vote = post.user_votes[0].value
                    else:
                        post.user_vote = None
            else:
                for post in results:
                    post.user_vote = None

        elif search_type == 'communities':
            communities_qs = Community.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            ).order_by('-member_count')

            paginator = Paginator(communities_qs, 10)
            results = paginator.get_page(page)
            total_count = paginator.count

        elif search_type == 'users':
            users_qs = User.objects.filter(
                Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query),
                is_active=True
            ).select_related('profile').order_by('username')

            paginator = Paginator(users_qs, 10)
            results = paginator.get_page(page)
            total_count = paginator.count

            if request.user.is_authenticated:
                following_ids = set(request.user.following.values_list('following_id', flat=True))
                for user_obj in results:
                    user_obj.is_following = user_obj.id in following_ids
            else:
                for user_obj in results:
                    user_obj.is_following = False

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
        # Поиск по постам
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

        # Поиск по сообществам
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]

        for community in communities:
            suggestions.append({
                'type': 'community',
                'title': community.name,
                'subtitle': f'{community.member_count} участников',
                'url': community.get_absolute_url(),
            })

        # Поиск по пользователям
        users = User.objects.filter(
            username__icontains=query,
            is_active=True
        )[:3]

        for user_obj in users:
            suggestions.append({
                'type': 'user',
                'title': user_obj.username,
                'subtitle': f'Карма: {user_obj.karma}',
                'url': user_obj.get_absolute_url(),
            })

    context = {
        'query': query,
        'suggestions': suggestions,
    }
    return render(request, 'search/partials/suggestions.html', context)

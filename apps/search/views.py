from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User
from apps.votes.models import PostVote


def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if len(query) >= 2:
        # Посты
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community')[:3]
        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}',
            })

        # Сообщества
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]
        for community in communities:
            suggestions.append({
                'url': community.get_absolute_url(),
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
            })

        # Пользователи
        users = User.objects.filter(
            username__icontains=query
        )[:3]
        for user in users:
            suggestions.append({
                'url': user.get_absolute_url(),
                'type': 'user',
                'title': f'u/{user.username}',
                'subtitle': f'Карма: {user.karma}',
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query,
    })


def search_results(request):
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    page_number = request.GET.get('page', 1)

    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    if not query:
        return render(request, 'search/results.html', {
            'query': query,
            'search_type': search_type,
            'error': 'Введите поисковый запрос',
        })

    results = []
    total_count = 0

    if search_type == 'posts':
        queryset = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('author', 'community').order_by('-created_at')

        if request.user.is_authenticated:
            user_votes = PostVote.objects.filter(user=request.user)
            queryset = queryset.prefetch_related(
                Prefetch('votes', queryset=user_votes, to_attr='user_votes')
            )

        paginator = Paginator(queryset, 10)
        results = paginator.get_page(page_number)
        total_count = paginator.count

        if request.user.is_authenticated:
            for post in results:
                votes = getattr(post, 'user_votes', [])
                post.user_vote = votes[0].value if votes else 0

    elif search_type == 'communities':
        queryset = Community.objects.filter(
            name__icontains=query
        ).order_by('-member_count')

        paginator = Paginator(queryset, 10)
        results = paginator.get_page(page_number)
        total_count = paginator.count

    elif search_type == 'users':
        queryset = User.objects.filter(
            username__icontains=query
        ).select_related('profile').order_by('-karma')

        paginator = Paginator(queryset, 10)
        results = paginator.get_page(page_number)
        total_count = paginator.count

        if request.user.is_authenticated:
            from apps.users.models import UserFollow
            following_ids = set(
                UserFollow.objects.filter(follower=request.user).values_list('following_id', flat=True)
            )
            for user in results:
                user.is_following = user.id in following_ids

    return render(request, 'search/results.html', {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
    })

from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_results(request):
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    page_number = request.GET.get('page', 1)
    
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    results = []
    total_count = 0
    error = None

    if not query:
        error = "Введите поисковый запрос"
    else:
        if search_type == 'posts':
            qs = Post.objects.filter(
                title__icontains=query,
                is_deleted=False
            ).select_related('author', 'community').order_by('-created_at')

            if request.user.is_authenticated:
                user_votes = PostVote.objects.filter(user=request.user)
                qs = qs.prefetch_related(
                    Prefetch('votes', queryset=user_votes, to_attr='user_votes')
                )

            paginator = Paginator(qs, 10)
            total_count = paginator.count
            results = paginator.get_page(page_number)

            if request.user.is_authenticated:
                for post in results:
                    post.user_vote = post.user_votes[0].value if getattr(post, 'user_votes', None) else 0

        elif search_type == 'communities':
            qs = Community.objects.filter(
                name__icontains=query,
                is_active=True
            ).order_by('-member_count')

            paginator = Paginator(qs, 10)
            total_count = paginator.count
            results = paginator.get_page(page_number)

        elif search_type == 'users':
            qs = User.objects.filter(
                username__icontains=query,
                is_active=True
            ).select_related('profile').prefetch_related('posts', 'comments').order_by('username')

            paginator = Paginator(qs, 10)
            total_count = paginator.count
            results = paginator.get_page(page_number)

            if request.user.is_authenticated:
                following_ids = set(
                    UserFollow.objects.filter(follower=request.user)
                    .values_list('following_id', flat=True)
                )
                for u in results:
                    u.is_following = u.id in following_ids

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
        'error': error,
    }
    return render(request, 'search/results.html', context)


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
            name__icontains=query,
            is_active=True
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
            username__icontains=query,
            is_active=True
        )[:3]

        for user in users:
            suggestions.append({
                'url': user.get_absolute_url(),
                'type': 'user',
                'title': f'u/{user.username}',
                'subtitle': f'Карма: {user.karma}',
            })

    context = {
        'query': query,
        'suggestions': suggestions,
    }
    return render(request, 'search/partials/suggestions.html', context)

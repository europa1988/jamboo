from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.urls import reverse

from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_results(request):
    """
    Полностраничный поиск по постам, сообществам и пользователям с пагинацией.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page_number = request.GET.get('page', 1)
    results = []
    total_count = 0
    error = None

    if query:
        if search_type == 'posts':
            posts_qs = Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                is_deleted=False
            ).select_related('author', 'community')

            if request.user.is_authenticated:
                user_votes = PostVote.objects.filter(user=request.user)
                posts_qs = posts_qs.prefetch_related(
                    Prefetch('votes', queryset=user_votes, to_attr='current_user_votes')
                )

            paginator = Paginator(posts_qs, 10)
            page_obj = paginator.get_page(page_number)

            if request.user.is_authenticated:
                for post in page_obj.object_list:
                    votes = getattr(post, 'current_user_votes', [])
                    post.user_vote = votes[0].value if votes else None

            results = page_obj
            total_count = paginator.count

        elif search_type == 'communities':
            communities_qs = Community.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query),
                is_active=True
            ).order_by('-member_count')

            paginator = Paginator(communities_qs, 10)
            page_obj = paginator.get_page(page_number)
            results = page_obj
            total_count = paginator.count

        elif search_type == 'users':
            users_qs = User.objects.filter(
                Q(username__icontains=query) | Q(profile__bio__icontains=query),
                is_active=True
            ).select_related('profile').order_by('-karma')

            paginator = Paginator(users_qs, 10)
            page_obj = paginator.get_page(page_number)

            if request.user.is_authenticated:
                following_ids = set(
                    UserFollow.objects.filter(
                        follower=request.user,
                        following__in=page_obj.object_list
                    ).values_list('following_id', flat=True)
                )
                for user_obj in page_obj.object_list:
                    user_obj.is_following = user_obj.id in following_ids

            results = page_obj
            total_count = paginator.count
    else:
        results = []
        total_count = 0

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
        'error': error,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX эндпоинт для автодополнения (подсказок) при поиске.
    """
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
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}',
            })

        # Сообщества
        communities = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        )[:3]

        for community in communities:
            suggestions.append({
                'url': reverse('communities:detail', kwargs={'slug': community.slug}),
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
            })

        # Пользователи
        users = User.objects.filter(
            username__icontains=query,
            is_active=True
        ).select_related('profile')[:3]

        for user in users:
            suggestions.append({
                'url': reverse('users:profile', kwargs={'username': user.username}),
                'type': 'user',
                'title': f'u/{user.username}',
                'subtitle': f'Карма: {user.karma}',
            })

    context = {
        'suggestions': suggestions,
        'query': query,
    }
    return render(request, 'search/partials/suggestions.html', context)


def autocomplete(request):
    """Алиас для обратной совместимости."""
    return search_suggestions(request)

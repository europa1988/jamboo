from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote

User = get_user_model()


def search_results(request):
    """
    Основное представление результатов поиска.
    Поддерживает поиск по постам, сообществам и пользователям с пагинацией.
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
                title__icontains=query,
                is_deleted=False
            ).select_related('author', 'community')

            if request.user.is_authenticated:
                user_votes = PostVote.objects.filter(user=request.user)
                posts_qs = posts_qs.prefetch_related(
                    Prefetch('votes', queryset=user_votes, to_attr='user_votes_list')
                )

            posts_qs = posts_qs.order_by('-created_at')
            paginator = Paginator(posts_qs, 10)
            results = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                for post in results:
                    user_votes_list = getattr(post, 'user_votes_list', None)
                    if user_votes_list is not None:
                        post.user_vote = user_votes_list[0].value if user_votes_list else None
                    else:
                        post.user_vote = post.get_user_vote(request.user)

        elif search_type == 'communities':
            communities_qs = Community.objects.filter(
                name__icontains=query,
                is_active=True
            ).order_by('-member_count')
            paginator = Paginator(communities_qs, 10)
            results = paginator.get_page(page_number)
            total_count = paginator.count

        elif search_type == 'users':
            users_qs = User.objects.filter(
                username__icontains=query,
                is_active=True
            ).select_related('profile').order_by('-karma', 'username')
            paginator = Paginator(users_qs, 10)
            results = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                following_ids = set(
                    request.user.following.values_list('following_id', flat=True)
                )
                for user_obj in results:
                    user_obj.is_following = user_obj.id in following_ids

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
    HTMX эндпоинт автокомплита поиска.
    Возвращает варианты подходок для постов, сообществ и пользователей.
    """
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
        ).order_by('-karma', 'username')[:3]
        for user_obj in users:
            suggestions.append({
                'url': user_obj.get_absolute_url(),
                'type': 'user',
                'title': f'u/{user_obj.username}',
                'subtitle': f'Карма: {user_obj.karma}',
            })

    context = {
        'suggestions': suggestions,
        'query': query,
    }
    return render(request, 'search/partials/suggestions.html', context)

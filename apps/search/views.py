from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch

from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_results(request):
    """
    Основное представление результатов поиска с вкладками и пагинацией.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page_number = request.GET.get('page', 1)
    results = []
    total_count = 0
    error = None

    if not query:
        error = 'Введите поисковый запрос'
    else:
        if search_type == 'posts':
            posts_qs = Post.objects.filter(
                title__icontains=query,
                is_deleted=False
            ).select_related('author', 'community')

            if request.user.is_authenticated:
                posts_qs = posts_qs.prefetch_related(
                    Prefetch('votes', queryset=PostVote.objects.filter(user=request.user), to_attr='current_user_votes')
                )

            posts_qs = posts_qs.order_by('-created_at')
            paginator = Paginator(posts_qs, 10)
            page_obj = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                for post in page_obj:
                    post.user_vote = post.get_user_vote(request.user)

            results = page_obj

        elif search_type == 'communities':
            communities_qs = Community.objects.filter(
                name__icontains=query
            ).order_by('-member_count', 'name')

            paginator = Paginator(communities_qs, 10)
            page_obj = paginator.get_page(page_number)
            total_count = paginator.count
            results = page_obj

        elif search_type == 'users':
            users_qs = User.objects.filter(
                username__icontains=query
            ).select_related('profile').order_by('username')

            paginator = Paginator(users_qs, 10)
            page_obj = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                following_ids = set(
                    UserFollow.objects.filter(
                        follower=request.user,
                        following__in=page_obj.object_list
                    ).values_list('following_id', flat=True)
                )
                for user_item in page_obj:
                    user_item.is_following = user_item.id in following_ids

            results = page_obj

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
    HTMX эндпоинт выпадающих подсказок поиска.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # 1. Посты (макс 3)
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

        # 2. Сообщества (макс 3)
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]

        for community in communities:
            suggestions.append({
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
                'url': community.get_absolute_url(),
            })

        # 3. Пользователи (макс 3)
        users = User.objects.filter(
            username__icontains=query
        )[:3]

        for user_item in users:
            suggestions.append({
                'type': 'user',
                'title': f'u/{user_item.username}',
                'subtitle': f'Карма: {user_item.karma}',
                'url': user_item.get_absolute_url(),
            })

    context = {
        'query': query,
        'suggestions': suggestions,
    }
    return render(request, 'search/partials/suggestions.html', context)

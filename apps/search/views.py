from django.shortcuts import render
from django.core.paginator import Paginator
from django.urls import reverse
from django.db.models import Prefetch

from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_results(request):
    """
    Основное представление результатов поиска.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts').strip()
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page_number = request.GET.get('page', 1)
    results_page = None
    total_count = 0
    error = None

    if query:
        if search_type == 'posts':
            queryset = Post.objects.filter(
                title__icontains=query,
                is_deleted=False
            ).select_related('author', 'community').order_by('-created_at')

            if request.user.is_authenticated:
                queryset = queryset.prefetch_related(
                    Prefetch('votes', queryset=PostVote.objects.filter(user=request.user))
                )

            paginator = Paginator(queryset, 10)
            results_page = paginator.get_page(page_number)
            total_count = paginator.count

            # Вычисляем user_vote после пагинации
            if request.user.is_authenticated:
                for post in results_page:
                    user_vote_obj = post.votes.all()
                    post.user_vote = user_vote_obj[0].value if user_vote_obj else None
            else:
                for post in results_page:
                    post.user_vote = None

        elif search_type == 'communities':
            queryset = Community.objects.filter(
                name__icontains=query
            ).order_by('-member_count')

            paginator = Paginator(queryset, 10)
            results_page = paginator.get_page(page_number)
            total_count = paginator.count

        elif search_type == 'users':
            queryset = User.objects.filter(
                username__icontains=query
            ).select_related('profile').order_by('username')

            paginator = Paginator(queryset, 10)
            results_page = paginator.get_page(page_number)
            total_count = paginator.count

            # Вычисляем is_following после пагинации
            if request.user.is_authenticated:
                following_ids = set(
                    UserFollow.objects.filter(
                        follower=request.user,
                        following__in=[u.id for u in results_page]
                    ).values_list('following_id', flat=True)
                )
                for profile_user in results_page:
                    profile_user.is_following = profile_user.id in following_ids
            else:
                for profile_user in results_page:
                    profile_user.is_following = False

    context = {
        'query': query,
        'search_type': search_type,
        'results': results_page,
        'total_count': total_count,
        'error': error,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX эндпоинт для выпадающих подсказок поиска.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # 3 поста
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community').order_by('-created_at')[:3]

        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}',
            })

        # 3 сообщества
        communities = Community.objects.filter(
            name__icontains=query
        ).order_by('-member_count')[:3]

        for community in communities:
            suggestions.append({
                'url': reverse('communities:detail', kwargs={'slug': community.slug}),
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
            })

        # 3 пользователя
        users = User.objects.filter(
            username__icontains=query
        ).order_by('username')[:3]

        for profile_user in users:
            suggestions.append({
                'url': reverse('users:profile', kwargs={'username': profile_user.username}),
                'type': 'user',
                'title': f'u/{profile_user.username}',
                'subtitle': f'Карма: {profile_user.karma}',
            })

    context = {
        'suggestions': suggestions,
        'query': query,
    }
    return render(request, 'search/partials/suggestions.html', context)

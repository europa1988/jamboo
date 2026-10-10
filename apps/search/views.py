from django.shortcuts import render
from django.core.paginator import Paginator
from django.urls import reverse
from django.db.models import Prefetch

from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_results(request):
    """Страница результатов поиска."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page_number = request.GET.get('page', 1)
    results = []
    total_count = 0
    error = None

    if not query:
        error = 'Пожалуйста, введите поисковый запрос.'
    else:
        if search_type == 'posts':
            qs = Post.objects.filter(
                title__icontains=query,
                is_deleted=False
            ).select_related('author', 'community').order_by('-created_at')

            if request.user.is_authenticated:
                qs = qs.prefetch_related(
                    Prefetch(
                        'votes',
                        queryset=PostVote.objects.filter(user=request.user),
                        to_attr='user_votes'
                    )
                )

            paginator = Paginator(qs, 10)
            results = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                for post in results:
                    post.user_vote = post.user_votes[0].value if getattr(post, 'user_votes', None) else None

        elif search_type == 'communities':
            qs = Community.objects.filter(
                name__icontains=query
            ).order_by('-member_count', 'name')

            paginator = Paginator(qs, 10)
            results = paginator.get_page(page_number)
            total_count = paginator.count

        elif search_type == 'users':
            qs = User.objects.filter(
                username__icontains=query
            ).select_related('profile').order_by('username')

            paginator = Paginator(qs, 10)
            results = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                user_ids = [u.id for u in results]
                following_ids = set(
                    UserFollow.objects.filter(
                        follower=request.user,
                        following_id__in=user_ids
                    ).values_list('following_id', flat=True)
                )
                for profile_user in results:
                    profile_user.is_following = profile_user.id in following_ids

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
        'error': error,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """HTMX эндпоинт подсказок поиска (автокомплит)."""
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # Посты
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community').order_by('-created_at')[:3]

        for post in posts:
            suggestions.append({
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}',
                'url': post.get_absolute_url(),
            })

        # Сообщества
        communities = Community.objects.filter(
            name__icontains=query
        ).order_by('-member_count', 'name')[:3]

        for comm in communities:
            suggestions.append({
                'type': 'community',
                'title': f'c/{comm.name}',
                'subtitle': f'{comm.member_count} участников',
                'url': reverse('communities:detail', kwargs={'slug': comm.slug}),
            })

        # Пользователи
        users = User.objects.filter(
            username__icontains=query
        ).order_by('username')[:3]

        for u in users:
            suggestions.append({
                'type': 'user',
                'title': f'u/{u.username}',
                'subtitle': f'Карма: {u.karma}',
                'url': reverse('users:profile', kwargs={'username': u.username}),
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query,
    })

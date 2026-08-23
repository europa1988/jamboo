from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.urls import reverse
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_results(request):
    """Страница результатов поиска с фильтрацией по типам и пагинацией."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')

    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    context = {
        'query': query,
        'search_type': search_type,
        'results': None,
        'total_count': 0,
        'error': None,
    }

    if not query:
        return render(request, 'search/results.html', context)

    if search_type == 'posts':
        posts_qs = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('author', 'community').order_by('-created_at')

        if request.user.is_authenticated:
            posts_qs = posts_qs.prefetch_related(
                Prefetch(
                    'votes',
                    queryset=PostVote.objects.filter(user=request.user),
                    to_attr='user_votes'
                )
            )

        paginator = Paginator(posts_qs, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        if request.user.is_authenticated:
            for post in page_obj:
                votes = getattr(post, 'user_votes', [])
                post.user_vote = votes[0] if votes else None

        context['results'] = page_obj
        context['total_count'] = paginator.count

    elif search_type == 'communities':
        communities_qs = Community.objects.filter(
            name__icontains=query
        ).order_by('-member_count')

        paginator = Paginator(communities_qs, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['results'] = page_obj
        context['total_count'] = paginator.count

    elif search_type == 'users':
        users_qs = User.objects.filter(
            username__icontains=query
        ).select_related('profile').order_by('-karma', 'username')

        paginator = Paginator(users_qs, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        if request.user.is_authenticated:
            user_ids = [u.id for u in page_obj]
            following_set = set(
                UserFollow.objects.filter(
                    follower=request.user,
                    following_id__in=user_ids
                ).values_list('following_id', flat=True)
            )
            for u in page_obj:
                u.is_following = u.id in following_set

        context['results'] = page_obj
        context['total_count'] = paginator.count

    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """HTMX эндпоинт выпадающих подсказок поиска."""
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
                'title': post.title,
                'subtitle': f'c/{post.community.name}',
                'type': 'post',
                'url': post.get_absolute_url()
            })

        # Сообщества
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]

        for community in communities:
            suggestions.append({
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
                'type': 'community',
                'url': reverse('communities:detail', kwargs={'slug': community.slug})
            })

        # Пользователи
        users = User.objects.filter(
            username__icontains=query
        )[:3]

        for user in users:
            suggestions.append({
                'title': f'u/{user.username}',
                'subtitle': f'Карма: {user.karma}',
                'type': 'user',
                'url': reverse('users:profile', kwargs={'username': user.username})
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query,
    })

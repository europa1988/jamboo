from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.urls import reverse

from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_results(request):
    """Полностраничные результаты поиска."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    context = {
        'query': query,
        'search_type': search_type,
        'error': None,
        'results': None,
        'total_count': 0,
    }

    if not query:
        context['error'] = 'Введите поисковый запрос.'
        return render(request, 'search/results.html', context)

    if len(query) < 2:
        context['error'] = 'Запрос должен быть не менее 2 символов.'
        return render(request, 'search/results.html', context)

    if search_type == 'posts':
        posts_qs = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('author', 'community')

        if request.user.is_authenticated:
            posts_qs = posts_qs.prefetch_related(
                Prefetch(
                    'votes',
                    queryset=PostVote.objects.filter(user=request.user),
                    to_attr='user_votes'
                )
            )

        paginator = Paginator(posts_qs, 10)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        # Вычисляем свойства после пагинации
        for post in page_obj.object_list:
            if request.user.is_authenticated:
                post.user_vote = post.user_votes[0].value if post.user_votes else None
            else:
                post.user_vote = None

        context['results'] = page_obj
        context['total_count'] = paginator.count

    elif search_type == 'communities':
        communities_qs = Community.objects.filter(
            name__icontains=query
        ).order_by('-member_count')

        paginator = Paginator(communities_qs, 10)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        context['results'] = page_obj
        context['total_count'] = paginator.count

    elif search_type == 'users':
        users_qs = User.objects.filter(
            username__icontains=query
        ).order_by('username').select_related('profile')

        paginator = Paginator(users_qs, 10)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        # Вычисляем свойства после пагинации
        if request.user.is_authenticated:
            user_ids = [u.id for u in page_obj.object_list]
            following_ids = set(
                UserFollow.objects.filter(
                    follower=request.user,
                    following_id__in=user_ids
                ).values_list('following_id', flat=True)
            )
            for u in page_obj.object_list:
                u.is_following = u.id in following_ids
        else:
            for u in page_obj.object_list:
                u.is_following = False

        context['results'] = page_obj
        context['total_count'] = paginator.count

    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """HTMX эндпоинт автокомплита поиска."""
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # Поиск по постам (до 5)
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('author', 'community')[:5]
        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f"c/{post.community.name} • u/{post.author.username}"
            })

        # Поиск по сообществам (до 3)
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]
        for community in communities:
            suggestions.append({
                'url': reverse('communities:detail', kwargs={'slug': community.slug}),
                'type': 'community',
                'title': f"c/{community.name}",
                'subtitle': f"{community.member_count} участников"
            })

        # Поиск по пользователям (до 3)
        users = User.objects.filter(
            username__icontains=query
        ).order_by('username')[:3]
        for user in users:
            suggestions.append({
                'url': reverse('users:profile', kwargs={'username': user.username}),
                'type': 'user',
                'title': f"u/{user.username}",
                'subtitle': f"Карма: {user.karma}"
            })

    context = {
        'suggestions': suggestions,
        'query': query
    }
    return render(request, 'search/partials/suggestions.html', context)

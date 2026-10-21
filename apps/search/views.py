from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Prefetch
from django.shortcuts import render
from django.urls import reverse

from apps.communities.models import Community
from apps.posts.models import Post
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_results(request):
    """
    Полностраничный поиск с пагинацией по постам, сообществам и пользователям.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page = request.GET.get('page', 1)
    results = []
    total_count = 0

    if query:
        if search_type == 'posts':
            queryset = Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                is_deleted=False
            ).select_related('author', 'community')

            if request.user.is_authenticated:
                user_votes = PostVote.objects.filter(user=request.user)
                queryset = queryset.prefetch_related(
                    Prefetch('votes', queryset=user_votes, to_attr='current_user_votes')
                )

            queryset = queryset.order_by('-created_at')

        elif search_type == 'communities':
            queryset = Community.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            ).order_by('-member_count', 'name')

        elif search_type == 'users':
            queryset = User.objects.filter(
                username__icontains=query
            ).select_related('profile').order_by('id')

        paginator = Paginator(queryset, 10)
        total_count = paginator.count

        try:
            results = paginator.page(page)
        except PageNotAnInteger:
            results = paginator.page(1)
        except EmptyPage:
            results = paginator.page(paginator.num_pages)

        # Дополняем элементы текущей страницы необходимыми атрибутами
        if search_type == 'posts' and request.user.is_authenticated:
            for post in results:
                votes = getattr(post, 'current_user_votes', [])
                post.user_vote = votes[0].value if votes else None

        elif search_type == 'users' and request.user.is_authenticated:
            page_users = list(results)
            following_ids = set(
                UserFollow.objects.filter(
                    follower=request.user,
                    following__in=page_users
                ).values_list('following_id', flat=True)
            )
            for page_user in results:
                page_user.is_following = page_user.id in following_ids

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX эндпоинт для автодополнения (подсказок) поиска.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # Посты (до 3)
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

        # Сообщества (до 3)
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]
        for community in communities:
            suggestions.append({
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
                'url': reverse('communities:detail', kwargs={'slug': community.slug}),
            })

        # Пользователи (до 3)
        users = User.objects.filter(
            username__icontains=query
        ).order_by('id')[:3]
        for user in users:
            suggestions.append({
                'type': 'user',
                'title': f'u/{user.username}',
                'subtitle': f'Карма: {user.karma}',
                'url': reverse('users:profile', kwargs={'username': user.username}),
            })

    context = {
        'suggestions': suggestions,
        'query': query,
    }
    return render(request, 'search/partials/suggestions.html', context)

from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse

from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow


def search_results(request):
    """Страница результатов поиска."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'
    
    page = request.GET.get('page', 1)
    results = []
    total_count = 0

    if query:
        if search_type == 'posts':
            posts = Post.objects.filter(
                is_deleted=False
            ).filter(
                Q(title__icontains=query) | Q(content__icontains=query)
            ).select_related('author', 'community').prefetch_related('votes').order_by('-created_at')

            total_count = posts.count()
            paginator = Paginator(posts, 10)
            results = paginator.get_page(page)

            if request.user.is_authenticated:
                for post in results:
                    post.user_vote = post.get_user_vote(request.user)

        elif search_type == 'communities':
            communities = Community.objects.filter(
                is_active=True
            ).filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            ).order_by('-member_count', 'id')

            total_count = communities.count()
            paginator = Paginator(communities, 10)
            results = paginator.get_page(page)

        elif search_type == 'users':
            users = User.objects.filter(
                Q(username__icontains=query) | Q(profile__bio__icontains=query)
            ).select_related('profile').order_by('username')

            total_count = users.count()
            paginator = Paginator(users, 10)
            results = paginator.get_page(page)

            if request.user.is_authenticated:
                following_ids = set(
                    UserFollow.objects.filter(
                        follower=request.user,
                        following_id__in=[u.id for u in results]
                    ).values_list('following_id', flat=True)
                )
                for user in results:
                    user.is_following = user.id in following_ids

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """HTMX эндпоинт автокомплита поиска."""
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # Поиск по постам
        posts = Post.objects.filter(
            is_deleted=False
        ).filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        ).select_related('community').order_by('-created_at')[:3]

        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}',
            })

        # Поиск по сообществам
        communities = Community.objects.filter(
            is_active=True
        ).filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).order_by('-member_count', 'id')[:3]

        for community in communities:
            suggestions.append({
                'url': reverse('communities:detail', kwargs={'slug': community.slug}),
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
            })

        # Поиск по пользователям
        users = User.objects.filter(
            Q(username__icontains=query) | Q(profile__bio__icontains=query)
        ).order_by('username')[:3]

        for user in users:
            suggestions.append({
                'url': reverse('users:profile', kwargs={'username': user.username}),
                'type': 'user',
                'title': f'u/{user.username}',
                'subtitle': f'Карма: {user.karma}',
            })

    context = {
        'query': query,
        'suggestions': suggestions,
    }
    return render(request, 'search/partials/suggestions.html', context)

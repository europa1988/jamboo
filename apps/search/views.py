from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community

User = get_user_model()


def search_results(request):
    """
    Основное представление поиска по постам, сообществам и пользователям.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts').strip()
    page_number = request.GET.get('page', 1)

    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    results = []
    total_count = 0

    if query:
        if search_type == 'posts':
            queryset = Post.objects.filter(
                is_deleted=False
            ).filter(
                Q(title__icontains=query) | Q(content__icontains=query)
            ).select_related('author', 'community').order_by('-created_at')

            paginator = Paginator(queryset, 10)
            results = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                for post in results:
                    post.user_vote = post.get_user_vote(request.user)

        elif search_type == 'communities':
            queryset = Community.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            ).order_by('-member_count')

            paginator = Paginator(queryset, 10)
            results = paginator.get_page(page_number)
            total_count = paginator.count

        elif search_type == 'users':
            queryset = User.objects.filter(
                is_active=True,
                username__icontains=query
            ).select_related('profile').order_by('username')

            paginator = Paginator(queryset, 10)
            results = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                following_ids = set(request.user.following.values_list('following_id', flat=True))
                for profile_user in results:
                    profile_user.is_following = profile_user.id in following_ids

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
    }

    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX эндпоинт автокомплита поиска.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # Поиск по постам (до 3 результатов)
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('author', 'community').order_by('-created_at')[:3]

        for post in posts:
            suggestions.append({
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name} • u/{post.author.username}',
                'url': post.get_absolute_url()
            })

        # Поиск по сообществам (до 3 результатов)
        communities = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).order_by('-member_count')[:3]

        for community in communities:
            suggestions.append({
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
                'url': reverse('communities:detail', kwargs={'slug': community.slug})
            })

        # Поиск по пользователям (до 3 результатов)
        users = User.objects.filter(
            is_active=True,
            username__icontains=query
        ).order_by('username')[:3]

        for user in users:
            suggestions.append({
                'type': 'user',
                'title': f'u/{user.username}',
                'subtitle': f'Карма: {user.karma}',
                'url': reverse('users:profile', kwargs={'username': user.username})
            })

    context = {
        'suggestions': suggestions,
        'query': query,
    }

    return render(request, 'search/partials/suggestions.html', context)

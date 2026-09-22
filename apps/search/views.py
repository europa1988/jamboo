from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote

User = get_user_model()


def search_results(request):
    """
    Страница результатов поиска с поддержкой вкладок (посты, сообщества, пользователи) и пагинации.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts').strip()
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page = request.GET.get('page', 1)
    results = []
    total_count = 0

    if query:
        if search_type == 'posts':
            qs = Post.objects.filter(
                is_deleted=False
            ).filter(
                Q(title__icontains=query) | Q(content__icontains=query)
            ).select_related('author', 'community')

            if request.user.is_authenticated:
                qs = qs.prefetch_related(
                    Prefetch('votes', queryset=PostVote.objects.filter(user=request.user))
                )

            qs = qs.order_by('-created_at')
            paginator = Paginator(qs, 10)
            results = paginator.get_page(page)
            total_count = paginator.count

            if request.user.is_authenticated:
                for post in results:
                    post.user_vote = post.get_user_vote(request.user)

        elif search_type == 'communities':
            qs = Community.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            ).order_by('-member_count', '-created_at')

            paginator = Paginator(qs, 10)
            results = paginator.get_page(page)
            total_count = paginator.count

        elif search_type == 'users':
            qs = User.objects.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            ).order_by('username')

            paginator = Paginator(qs, 10)
            results = paginator.get_page(page)
            total_count = paginator.count

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
    }

    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX эндпоинт автокомплита / подсказок поиска.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # Поиск по постам
        posts = Post.objects.filter(
            is_deleted=False,
            title__icontains=query
        ).select_related('community').order_by('-created_at')[:3]

        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}'
            })

        # Поиск по сообществам
        communities = Community.objects.filter(
            name__icontains=query
        ).order_by('-member_count')[:3]

        for community in communities:
            suggestions.append({
                'url': community.get_absolute_url(),
                'type': 'community',
                'title': community.name,
                'subtitle': f'{community.member_count} участников'
            })

        # Поиск по пользователям
        users = User.objects.filter(
            username__icontains=query
        ).order_by('username')[:3]

        for user in users:
            suggestions.append({
                'url': user.get_absolute_url(),
                'type': 'user',
                'title': user.username,
                'subtitle': f'u/{user.username}'
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query
    })

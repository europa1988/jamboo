from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_results(request):
    """
    Полная страница результатов поиска с пагинацией по 10 элементов.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'
    
    page_number = request.GET.get('page', 1)
    results = None
    total_count = 0

    if query:
        if search_type == 'posts':
            qs = Post.objects.filter(
                is_deleted=False
            ).filter(
                Q(title__icontains=query) | Q(content__icontains=query)
            ).select_related('author', 'community').order_by('-created_at')

            if request.user.is_authenticated:
                qs = qs.prefetch_related(
                    Prefetch('votes', queryset=PostVote.objects.filter(user=request.user))
                )

            paginator = Paginator(qs, 10)
            results = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                for post in results:
                    post.user_vote = post.get_user_vote(request.user)

        elif search_type == 'communities':
            qs = Community.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            ).order_by('-member_count')

            paginator = Paginator(qs, 10)
            results = paginator.get_page(page_number)
            total_count = paginator.count

        elif search_type == 'users':
            qs = User.objects.filter(
                Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
            ).select_related('profile').order_by('username')

            paginator = Paginator(qs, 10)
            results = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                following_set = set(
                    UserFollow.objects.filter(
                        follower=request.user,
                        following__in=[u.id for u in results]
                    ).values_list('following_id', flat=True)
                )
                for u in results:
                    u.is_following = u.id in following_set

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX эндпоинт выпадающих подсказок поиска.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # Посты
        posts = Post.objects.filter(
            is_deleted=False,
            title__icontains=query
        ).select_related('community')[:3]

        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}' if post.community else ''
            })

        # Сообщества
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]

        for community in communities:
            suggestions.append({
                'url': community.get_absolute_url(),
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников'
            })

        # Пользователи
        users = User.objects.filter(
            username__icontains=query
        ).order_by('username')[:3]

        for user in users:
            suggestions.append({
                'url': user.get_absolute_url(),
                'type': 'user',
                'title': f'u/{user.username}',
                'subtitle': f'Карма: {user.karma}'
            })

    context = {
        'query': query,
        'suggestions': suggestions
    }
    return render(request, 'search/partials/suggestions.html', context)

from django.shortcuts import render
from django.core.paginator import Paginator
from django.urls import reverse
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow


def search_results(request):
    """
    Страница результатов поиска с поддержкой вкладок (посты, сообщества, пользователи) и пагинации.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page_number = request.GET.get('page', 1)
    error = None
    results = None
    total_count = 0

    if query:
        if len(query) < 2:
            error = 'Введите хотя бы 2 символа для поиска.'
        else:
            if search_type == 'posts':
                posts_qs = (
                    Post.objects.filter(title__icontains=query, is_deleted=False)
                    .select_related('author', 'community')
                    .prefetch_related('votes')
                    .order_by('-created_at')
                )
                paginator = Paginator(posts_qs, 10)
                results = paginator.get_page(page_number)
                total_count = paginator.count

                if request.user.is_authenticated:
                    for post in results:
                        post.user_vote = post.get_user_vote(request.user)

            elif search_type == 'communities':
                communities_qs = Community.objects.filter(
                    name__icontains=query
                ).order_by('-member_count', 'id')
                paginator = Paginator(communities_qs, 10)
                results = paginator.get_page(page_number)
                total_count = paginator.count

            elif search_type == 'users':
                users_qs = (
                    User.objects.filter(username__icontains=query, is_active=True)
                    .select_related('profile')
                    .order_by('username')
                )
                paginator = Paginator(users_qs, 10)
                results = paginator.get_page(page_number)
                total_count = paginator.count

                if request.user.is_authenticated:
                    following_ids = set(
                        UserFollow.objects.filter(
                            follower=request.user,
                            following__in=results.object_list
                        ).values_list('following_id', flat=True)
                    )
                    for user_obj in results:
                        user_obj.is_following = user_obj.id in following_ids

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
    HTMX-эндпоинт для автодополнения поиска.
    """
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
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}'
            })

        # Сообщества
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]

        for community in communities:
            suggestions.append({
                'url': reverse('communities:detail', kwargs={'slug': community.slug}),
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников'
            })

        # Пользователи
        users = User.objects.filter(
            username__icontains=query,
            is_active=True
        )[:3]

        for user_obj in users:
            suggestions.append({
                'url': reverse('users:profile', kwargs={'username': user_obj.username}),
                'type': 'user',
                'title': f'u/{user_obj.username}',
                'subtitle': f'Карма: {user_obj.karma}'
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query
    })

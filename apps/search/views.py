from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow


def search_results(request):
    """
    Основная страница поиска с вкладками и пагинацией.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    results = None
    total_count = 0
    error = None

    if not query:
        error = 'Введите поисковый запрос'
    else:
        page_number = request.GET.get('page', 1)

        if search_type == 'posts':
            posts_qs = Post.objects.filter(
                is_deleted=False
            ).filter(
                Q(title__icontains=query) | Q(content__icontains=query)
            ).select_related(
                'author', 'community'
            ).prefetch_related('votes').order_by('-created_at')

            total_count = posts_qs.count()
            paginator = Paginator(posts_qs, 10)
            page_obj = paginator.get_page(page_number)

            if request.user.is_authenticated:
                for post in page_obj:
                    post.user_vote = post.get_user_vote(request.user)

            results = page_obj

        elif search_type == 'communities':
            communities_qs = Community.objects.filter(
                is_active=True
            ).filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            ).order_by('-member_count')

            total_count = communities_qs.count()
            paginator = Paginator(communities_qs, 10)
            results = paginator.get_page(page_number)

        elif search_type == 'users':
            users_qs = User.objects.filter(
                is_active=True,
                username__icontains=query
            ).select_related('profile').order_by('username')

            total_count = users_qs.count()
            paginator = Paginator(users_qs, 10)
            page_obj = paginator.get_page(page_number)

            if request.user.is_authenticated:
                following_ids = set(
                    UserFollow.objects.filter(follower=request.user).values_list('following_id', flat=True)
                )
                for profile_user in page_obj:
                    profile_user.is_following = profile_user.id in following_ids

            results = page_obj

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
    HTMX эндпоинт автокомплита поиска.
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
                'url': post.get_absolute_url()
            })

        # Сообщества (до 3)
        communities = Community.objects.filter(
            name__icontains=query,
            is_active=True
        )[:3]
        for community in communities:
            suggestions.append({
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
                'url': community.get_absolute_url()
            })

        # Пользователи (до 3)
        users = User.objects.filter(
            username__icontains=query,
            is_active=True
        )[:3]
        for user in users:
            suggestions.append({
                'type': 'user',
                'title': f'u/{user.username}',
                'subtitle': f'Карма: {user.karma}',
                'url': user.get_absolute_url()
            })

    context = {
        'suggestions': suggestions,
        'query': query
    }
    
    return render(request, 'search/partials/suggestions.html', context)

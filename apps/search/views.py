from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_suggestions(request):
    """HTMX эндпоинт автокомплита / подсказок поиска."""
    query = request.GET.get('q', '').strip()
    
    suggestions = []
    
    if len(query) >= 2:
        # Поиск по постам
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
        
        # Поиск по сообществам
        communities = Community.objects.filter(
            is_active=True,
            name__icontains=query
        )[:3]
        
        for community in communities:
            suggestions.append({
                'url': community.get_absolute_url(),
                'type': 'community',
                'title': f'c/{community.name}',
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
                'title': f'u/{user.username}',
                'subtitle': f'Карма: {user.karma}'
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query
    })


def search_results(request):
    """Главная страница результатов поиска."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts').strip()

    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page_number = request.GET.get('page', 1)
    
    if not query:
        return render(request, 'search/results.html', {
            'query': '',
            'search_type': search_type,
            'results': None,
            'total_count': 0
        })

    if search_type == 'posts':
        posts_qs = Post.objects.filter(
            is_deleted=False
        ).filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        ).select_related('author', 'community').prefetch_related('votes').order_by('-created_at')

        paginator = Paginator(posts_qs, 10)
        results = paginator.get_page(page_number)
        total_count = paginator.count

        if request.user.is_authenticated:
            for post in results.object_list:
                post.user_vote = post.get_user_vote(request.user)

    elif search_type == 'communities':
        communities_qs = Community.objects.filter(
            is_active=True
        ).filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).order_by('-member_count', 'name')

        paginator = Paginator(communities_qs, 10)
        results = paginator.get_page(page_number)
        total_count = paginator.count

    elif search_type == 'users':
        users_qs = User.objects.filter(
            username__icontains=query
        ).select_related('profile').order_by('username')

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
            for profile_user in results.object_list:
                profile_user.is_following = profile_user.id in following_ids

    return render(request, 'search/results.html', {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count
    })

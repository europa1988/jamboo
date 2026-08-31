from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Prefetch
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote
from apps.users.models import UserFollow

User = get_user_model()


def search_results(request):
    """
    Основная страница результатов поиска.
    Поддерживает поиск по постам, сообществам и пользователям с пагинацией (10 на страницу).
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts').strip()
    page = request.GET.get('page', 1)
    
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    error = None
    results = []
    total_count = 0

    if not query:
        error = 'Пожалуйста, введите поисковый запрос.'
    else:
        if search_type == 'posts':
            qs = Post.objects.filter(
                title__icontains=query,
                is_deleted=False
            ).select_related('author', 'community')

            if request.user.is_authenticated:
                user_votes = PostVote.objects.filter(user=request.user)
                qs = qs.prefetch_related(Prefetch('votes', queryset=user_votes, to_attr='current_user_votes'))

            qs = qs.order_by('-created_at')
            paginator = Paginator(qs, 10)
            try:
                results = paginator.page(page)
            except (PageNotAnInteger, EmptyPage):
                results = paginator.page(1)

            total_count = paginator.count

            if request.user.is_authenticated:
                for post in results:
                    votes = getattr(post, 'current_user_votes', [])
                    post.user_vote = votes[0].value if votes else None

        elif search_type == 'communities':
            qs = Community.objects.filter(
                name__icontains=query
            ).order_by('-member_count', 'name')

            paginator = Paginator(qs, 10)
            try:
                results = paginator.page(page)
            except (PageNotAnInteger, EmptyPage):
                results = paginator.page(1)

            total_count = paginator.count

        elif search_type == 'users':
            qs = User.objects.filter(
                username__icontains=query
            ).select_related('profile').order_by('-date_joined')

            paginator = Paginator(qs, 10)
            try:
                results = paginator.page(page)
            except (PageNotAnInteger, EmptyPage):
                results = paginator.page(1)

            total_count = paginator.count

            if request.user.is_authenticated:
                page_user_ids = [u.id for u in results]
                following_ids = set(
                    UserFollow.objects.filter(
                        follower=request.user,
                        following_id__in=page_user_ids
                    ).values_list('following_id', flat=True)
                )
                for profile_user in results:
                    profile_user.is_following = profile_user.id in following_ids

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
    HTMX эндпоинт выпадающих подсказок поиска.
    Возвращает suggestions с полями url, type, title, subtitle.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if len(query) >= 2:
        # Посты
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community').order_by('-created_at')[:3]
        
        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f'в c/{post.community.name}',
            })

        # Сообщества
        communities = Community.objects.filter(
            name__icontains=query
        ).order_by('-member_count', 'name')[:3]
        
        for community in communities:
            suggestions.append({
                'url': f'/c/{community.slug}/',
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
            })

        # Пользователи
        users = User.objects.filter(
            username__icontains=query
        ).order_by('-date_joined')[:3]

        for user_obj in users:
            suggestions.append({
                'url': f'/u/{user_obj.username}/',
                'type': 'user',
                'title': f'u/{user_obj.username}',
                'subtitle': f'Карма: {user_obj.karma}',
            })

    context = {
        'suggestions': suggestions,
        'query': query,
    }
    return render(request, 'search/partials/suggestions.html', context)

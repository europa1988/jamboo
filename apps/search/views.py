from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.urls import reverse

from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_results(request):
    """
    Полностраничный поиск с пагинацией (10 результатов на страницу).
    Поддерживает поиск по постам (по умолчанию), сообществам и пользователям.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts').strip()

    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    results = None
    total_count = 0
    error = None
    
    if query:
        if search_type == 'posts':
            posts = Post.objects.filter(
                title__icontains=query,
                is_deleted=False
            ).select_related('author', 'community')

            # Оптимизация производительности: prefetch голосов текущего пользователя
            if request.user.is_authenticated:
                user_votes = PostVote.objects.filter(user=request.user)
                posts = posts.prefetch_related(Prefetch('votes', queryset=user_votes, to_attr='prefetched_votes'))

            total_count = posts.count()
            paginator = Paginator(posts, 10)
            page_number = request.GET.get('page')
            results = paginator.get_page(page_number)

            # Прикрепляем user_vote к постам на текущей странице без N+1 запросов
            if request.user.is_authenticated:
                for post in results:
                    vote = post.prefetched_votes[0] if hasattr(post, 'prefetched_votes') and post.prefetched_votes else None
                    post.user_vote = vote.value if vote else None

        elif search_type == 'communities':
            communities = Community.objects.filter(name__icontains=query, is_active=True).order_by('name')
            total_count = communities.count()
            paginator = Paginator(communities, 10)
            page_number = request.GET.get('page')
            results = paginator.get_page(page_number)

        elif search_type == 'users':
            users = User.objects.filter(username__icontains=query).select_related('profile').order_by('username')
            total_count = users.count()
            paginator = Paginator(users, 10)
            page_number = request.GET.get('page')
            results = paginator.get_page(page_number)

            # Добавляем флаг подписки для авторизованного пользователя
            if request.user.is_authenticated:
                following_ids = set(
                    UserFollow.objects.filter(follower=request.user).values_list('following_id', flat=True)
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
    HTMX эндпоинт автодополнения для поиска.
    Возвращает список подсказок (посты, сообщества, пользователи).
    """
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if len(query) >= 2:
        # 1. Поиск по постам
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community', 'author')[:5]
        
        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f"в c/{post.community.name} от u/{post.author.username}"
            })

        # 2. Поиск по сообществам
        communities = Community.objects.filter(
            name__icontains=query,
            is_active=True
        )[:3]
        
        for community in communities:
            suggestions.append({
                'url': reverse('communities:detail', kwargs={'slug': community.slug}),
                'type': 'community',
                'title': f"c/{community.name}",
                'subtitle': f"{community.member_count} участников"
            })

        # 3. Поиск по пользователям
        users = User.objects.filter(
            username__icontains=query
        )[:3]

        for user in users:
            suggestions.append({
                'url': reverse('users:profile', kwargs={'username': user.username}),
                'type': 'user',
                'title': f"u/{user.username}",
                'subtitle': f"Карма: {user.karma}"
            })

    html = render_to_string('search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query
    }, request=request)
    return HttpResponse(html)

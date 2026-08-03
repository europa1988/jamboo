from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote

User = get_user_model()


def search_suggestions(request):
    """HTMX эндпоинт автокомплита поиска."""
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if len(query) >= 2:
        # Поиск по постам
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community')[:5]
        for p in posts:
            suggestions.append({
                'title': p.title,
                'subtitle': f'c/{p.community.name}',
                'url': p.get_absolute_url(),
                'type': 'post'
            })

        # Поиск по сообществам
        communities = Community.objects.filter(
            name__icontains=query,
            is_active=True
        )[:3]
        for c in communities:
            suggestions.append({
                'title': f'c/{c.name}',
                'subtitle': f'{c.member_count} участников',
                'url': reverse('communities:detail', kwargs={'slug': c.slug}),
                'type': 'community'
            })

        # Поиск по пользователям
        users = User.objects.filter(
            username__icontains=query,
            is_active=True
        ).order_by('username')[:3]
        for u in users:
            suggestions.append({
                'title': f'u/{u.username}',
                'subtitle': f'Карма: {u.karma}',
                'url': reverse('users:profile', kwargs={'username': u.username}),
                'type': 'user'
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query
    })


def search_results(request):
    """Страница результатов поиска (посты, сообщества, пользователи)."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'
        
    page_number = request.GET.get('page', 1)
    results_list = []

    if query:
        if search_type == 'posts':
            posts = Post.objects.filter(
                title__icontains=query,
                is_deleted=False
            ).select_related('author', 'community')

            # Оптимизация prefetch для PostVote
            if request.user.is_authenticated:
                user_votes_prefetch = Prefetch(
                    'votes',
                    queryset=PostVote.objects.filter(user=request.user),
                    to_attr='user_votes'
                )
                posts = posts.prefetch_related(user_votes_prefetch)

            posts = posts.order_by('-created_at')
            results_list = list(posts)

            # Установка user_vote
            for post in results_list:
                if request.user.is_authenticated:
                    post.user_vote = post.user_votes[0].value if post.user_votes else None
                else:
                    post.user_vote = None

        elif search_type == 'communities':
            results_list = Community.objects.filter(
                name__icontains=query,
                is_active=True
            ).order_by('-member_count')

        elif search_type == 'users':
            results_list = User.objects.filter(
                username__icontains=query,
                is_active=True
            ).order_by('username')

    total_count = len(results_list) if isinstance(results_list, list) else results_list.count()

    paginator = Paginator(results_list, 10)
    page_obj = paginator.get_page(page_number)
    
    # Установка is_following динамически только для объектов на текущей странице (для оптимальной производительности и корректности)
    if search_type == 'users':
        if request.user.is_authenticated:
            from apps.users.models import UserFollow
            following_ids = set(
                UserFollow.objects.filter(follower=request.user).values_list('following_id', flat=True)
            )
            for u in page_obj.object_list:
                u.is_following = u.id in following_ids
        else:
            for u in page_obj.object_list:
                u.is_following = False

    context = {
        'query': query,
        'search_type': search_type,
        'results': page_obj,
        'total_count': total_count,
    }
    return render(request, 'search/results.html', context)

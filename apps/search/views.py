from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.urls import reverse
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User
from apps.votes.models import PostVote


def search_results(request):
    """
    Основной view поиска с вкладками (посты, сообщества, пользователи) и пагинацией.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    page_number = request.GET.get('page', 1)

    if not query:
        context = {
            'query': query,
            'search_type': search_type,
            'error': 'Введите поисковый запрос',
            'results': [],
            'total_count': 0,
        }
        return render(request, 'search/results.html', context)

    results = []
    total_count = 0

    if search_type == 'posts':
        qs = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('author', 'community').order_by('-created_at')

        if request.user.is_authenticated:
            qs = qs.prefetch_related(
                Prefetch(
                    'votes',
                    queryset=PostVote.objects.filter(user=request.user),
                    to_attr='user_votes'
                )
            )

        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(page_number)

        if request.user.is_authenticated:
            for post in page_obj:
                user_votes = getattr(post, 'user_votes', [])
                post.user_vote = user_votes[0].value if user_votes else None
        else:
            for post in page_obj:
                post.user_vote = None

        results = page_obj
        total_count = paginator.count

    elif search_type == 'communities':
        qs = Community.objects.filter(
            name__icontains=query
        ).order_by('-member_count')

        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(page_number)
        results = page_obj
        total_count = paginator.count

    elif search_type == 'users':
        qs = User.objects.filter(
            username__icontains=query
        ).select_related('profile').order_by('username')

        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(page_number)

        if request.user.is_authenticated:
            for u in page_obj:
                u.is_following = u.followers.filter(id=request.user.id).exists()
        else:
            for u in page_obj:
                u.is_following = False

        results = page_obj
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
    HTMX эндпоинт автокомплита поиска для предложений.
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
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}',
                'url': post.get_absolute_url(),
            })

        # Сообщества
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]

        for community in communities:
            community_url = (
                community.get_absolute_url()
                if hasattr(community, 'get_absolute_url')
                else reverse('communities:detail', kwargs={'slug': community.slug})
            )
            suggestions.append({
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
                'url': community_url,
            })

        # Пользователи
        users = User.objects.filter(
            username__icontains=query
        )[:3]

        for user_obj in users:
            user_url = (
                user_obj.get_absolute_url()
                if hasattr(user_obj, 'get_absolute_url')
                else reverse('users:profile', kwargs={'username': user_obj.username})
            )
            suggestions.append({
                'type': 'user',
                'title': f'u/{user_obj.username}',
                'subtitle': f'Карма: {user_obj.karma}',
                'url': user_url,
            })

    context = {
        'query': query,
        'suggestions': suggestions,
    }
    return render(request, 'search/partials/suggestions.html', context)

from django.shortcuts import render
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote

User = get_user_model()


def search_results(request):
    """
    Результаты поиска для постов, сообществ и пользователей.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts').strip()
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    results = []
    total_count = 0

    if search_type == 'posts':
        queryset = Post.objects.filter(is_deleted=False).select_related('community', 'author')
        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(content__icontains=query))

        queryset = queryset.order_by('-created_at')

        # Оптимизация prefetch для голосов
        if request.user.is_authenticated:
            post_votes_prefetch = Prefetch(
                'votes',
                queryset=PostVote.objects.filter(user=request.user),
                to_attr='user_votes'
            )
            queryset = queryset.prefetch_related(post_votes_prefetch)

        paginator = Paginator(queryset, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Заполнение user_vote для каждого поста во избежание N+1 запросов
        for post in page_obj:
            if request.user.is_authenticated:
                post.user_vote = post.user_votes[0].value if post.user_votes else None
            else:
                post.user_vote = None

        results = page_obj
        total_count = paginator.count

    elif search_type == 'communities':
        queryset = Community.objects.filter(is_active=True)
        if query:
            queryset = queryset.filter(Q(name__icontains=query) | Q(description__icontains=query))
        queryset = queryset.order_by('-member_count')

        paginator = Paginator(queryset, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        results = page_obj
        total_count = paginator.count

    elif search_type == 'users':
        queryset = User.objects.all()
        if query:
            queryset = queryset.filter(username__icontains=query)
        queryset = queryset.order_by('username')

        paginator = Paginator(queryset, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        if request.user.is_authenticated:
            # Предотвращение N+1 при проверке подписок
            following_ids = set(request.user.following.values_list('following_id', flat=True))
            for u in page_obj:
                u.is_following = u.id in following_ids
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
    HTMX эндпоинт автокомплита поиска.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # Поиск по постам
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community', 'author')[:5]
        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f"c/{post.community.name} • u/{post.author.username}"
            })

        # Поиск по сообществам
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

        # Поиск по пользователям
        users = User.objects.filter(
            username__icontains=query
        ).order_by('username')[:3]
        for user in users:
            suggestions.append({
                'url': reverse('users:profile', kwargs={'username': user.username}),
                'type': 'user',
                'title': f"u/{user.username}",
                'subtitle': f"Карма: {user.karma}"
            })

    context = {
        'suggestions': suggestions,
        'query': query,
    }
    return render(request, 'search/partials/suggestions.html', context)

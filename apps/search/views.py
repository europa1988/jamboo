from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Prefetch
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote
from apps.users.models import UserFollow

User = get_user_model()


def search_suggestions(request):
    """HTMX эндпоинт предложений поиска."""
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if len(query) >= 2:
        # 1. Посты
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('author', 'community')[:5]
        for p in posts:
            suggestions.append({
                'url': p.get_absolute_url(),
                'type': 'post',
                'title': p.title,
                'subtitle': f'c/{p.community.name} • u/{p.author.username}',
            })

        # 2. Сообщества
        communities = Community.objects.filter(
            name__icontains=query,
            is_active=True
        )[:3]
        for c in communities:
            suggestions.append({
                'url': reverse('communities:detail', kwargs={'slug': c.slug}),
                'type': 'community',
                'title': f'c/{c.name}',
                'subtitle': f'Участников: {c.member_count}',
            })

        # 3. Пользователи
        users = User.objects.filter(
            username__icontains=query,
            is_active=True
        )[:3]
        for u in users:
            suggestions.append({
                'url': reverse('users:profile', kwargs={'username': u.username}),
                'type': 'user',
                'title': f'u/{u.username}',
                'subtitle': f'Карма: {u.karma}',
            })

    context = {
        'suggestions': suggestions,
        'query': query,
    }
    return render(request, 'search/partials/suggestions.html', context)


def search_results(request):
    """Страница результатов поиска."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'
        
    error = None
    results = []
    total_count = 0
    
    if not query:
        error = "Введите поисковый запрос"
    elif len(query) < 2:
        error = "Запрос слишком короткий (минимум 2 символа)"
    else:
        if search_type == 'posts':
            posts_queryset = Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                is_deleted=False
            ).select_related('author', 'community')

            if request.user.is_authenticated:
                posts_queryset = posts_queryset.prefetch_related(
                    Prefetch('votes', queryset=PostVote.objects.filter(user=request.user), to_attr='user_votes')
                )

            posts_queryset = posts_queryset.order_by('-created_at')

            # Пагинация
            paginator = Paginator(posts_queryset, 10)
            page = request.GET.get('page')
            try:
                results = paginator.page(page)
            except PageNotAnInteger:
                results = paginator.page(1)
            except EmptyPage:
                results = paginator.page(paginator.num_pages)

            total_count = paginator.count

            # Проставляем user_vote
            for post in results:
                if request.user.is_authenticated and hasattr(post, 'user_votes') and post.user_votes:
                    post.user_vote = post.user_votes[0].value
                else:
                    post.user_vote = None

        elif search_type == 'communities':
            communities_queryset = Community.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query),
                is_active=True
            ).order_by('-member_count', 'name')

            paginator = Paginator(communities_queryset, 10)
            page = request.GET.get('page')
            try:
                results = paginator.page(page)
            except PageNotAnInteger:
                results = paginator.page(1)
            except EmptyPage:
                results = paginator.page(paginator.num_pages)

            total_count = paginator.count

        elif search_type == 'users':
            users_queryset = User.objects.filter(
                Q(username__icontains=query) | Q(profile__bio__icontains=query),
                is_active=True
            ).select_related('profile').prefetch_related('posts', 'comments').order_by('-karma', 'username')

            paginator = Paginator(users_queryset, 10)
            page = request.GET.get('page')
            try:
                results = paginator.page(page)
            except PageNotAnInteger:
                results = paginator.page(1)
            except EmptyPage:
                results = paginator.page(paginator.num_pages)

            total_count = paginator.count

            # Проставляем is_following
            if request.user.is_authenticated:
                following_ids = set(
                    UserFollow.objects.filter(follower=request.user).values_list('following_id', flat=True)
                )
                for u in results:
                    u.is_following = u.id in following_ids
            else:
                for u in results:
                    u.is_following = False

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
        'error': error,
    }
    return render(request, 'search/results.html', context)

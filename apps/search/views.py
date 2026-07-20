from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote
from apps.users.models import UserFollow

User = get_user_model()


def search_suggestions(request):
    """
    HTMX эндпоинт для автодополнения (suggestions).
    Ожидает список suggestions, где каждый элемент содержит:
    - url: ссылка на объект
    - type: 'post', 'community' или 'user'
    - title: заголовок/имя
    - subtitle: подзаголовок/описание
    """
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if len(query) >= 2:
        # Посты
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community', 'author')[:5]
        
        for p in posts:
            suggestions.append({
                'url': p.get_absolute_url(),
                'type': 'post',
                'title': p.title,
                'subtitle': f"c/{p.community.name} • u/{p.author.username}"
            })

        # Сообщества
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]
        
        for c in communities:
            suggestions.append({
                'url': reverse('communities:detail', kwargs={'slug': c.slug}),
                'type': 'community',
                'title': f"c/{c.name}",
                'subtitle': f"{c.member_count} участников"
            })

        # Пользователи
        users = User.objects.filter(
            username__icontains=query
        ).order_by('username')[:3]

        for u in users:
            suggestions.append({
                'url': reverse('users:profile', kwargs={'username': u.username}),
                'type': 'user',
                'title': f"u/{u.username}",
                'subtitle': f"Карма: {u.karma}"
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query
    })


def search_results(request):
    """
    Страница результатов поиска с поддержкой пагинации по 10 элементов
    и оптимизацией голосов для авторизованных пользователей.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    page_number = request.GET.get('page', 1)

    error = None
    results = []
    total_count = 0
    
    if not query:
        error = "Введите поисковый запрос для начала поиска"
    else:
        if search_type == 'posts':
            posts_qs = Post.objects.filter(
                title__icontains=query,
                is_deleted=False
            ).select_related('community', 'author')

            if request.user.is_authenticated:
                user_votes = PostVote.objects.filter(user=request.user)
                posts_qs = posts_qs.prefetch_related(
                    Prefetch('votes', queryset=user_votes, to_attr='user_votes')
                )

            # Обязательная явная сортировка для стабильной пагинации
            posts_qs = posts_qs.order_by('-created_at')

            paginator = Paginator(posts_qs, 10)
            page_obj = paginator.get_page(page_number)

            # Маппинг user_vote из prefetched-запроса
            if request.user.is_authenticated:
                for post in page_obj:
                    post.user_vote = post.user_votes[0].value if getattr(post, 'user_votes', None) else None
            else:
                for post in page_obj:
                    post.user_vote = None

            results = page_obj
            total_count = paginator.count

        elif search_type == 'communities':
            communities_qs = Community.objects.filter(
                name__icontains=query
            ).order_by('-member_count')

            paginator = Paginator(communities_qs, 10)
            page_obj = paginator.get_page(page_number)

            results = page_obj
            total_count = paginator.count

        elif search_type == 'users':
            users_qs = User.objects.filter(
                username__icontains=query
            ).order_by('username')

            paginator = Paginator(users_qs, 10)
            page_obj = paginator.get_page(page_number)

            if request.user.is_authenticated:
                following_ids = set(
                    UserFollow.objects.filter(follower=request.user)
                    .values_list('following_id', flat=True)
                )
                for u in page_obj:
                    u.is_following = u.id in following_ids
            else:
                for u in page_obj:
                    u.is_following = False

            results = page_obj
            total_count = paginator.count

        else:
            error = f"Неизвестный тип поиска: {search_type}"

    return render(request, 'search/results.html', {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
        'error': error
    })

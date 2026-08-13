from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote
from apps.users.models import UserFollow

User = get_user_model()


def search_results(request):
    """
    Полностраничный поиск с пагинацией (10 результатов на страницу).
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts').strip()

    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    results = None
    total_count = 0
    
    if query:
        if search_type == 'posts':
            # Фильтруем неудаленные посты по заголовку или тексту
            qs = Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                is_deleted=False
            ).select_related('author', 'community')

            # Оптимизация производительности: prefetch для PostVote для авторизованных пользователей
            if request.user.is_authenticated:
                qs = qs.prefetch_related(
                    Prefetch(
                        'votes',
                        queryset=PostVote.objects.filter(user=request.user),
                        to_attr='user_votes'
                    )
                )

            qs = qs.order_by('-created_at')

            # Пагинация (10 элементов на страницу)
            paginator = Paginator(qs, 10)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)

            # Добавление user_vote ПОСЛЕ пагинации
            for post in page_obj:
                if request.user.is_authenticated:
                    votes = getattr(post, 'user_votes', [])
                    post.user_vote = votes[0].value if votes else None
                else:
                    post.user_vote = None

            results = page_obj
            total_count = paginator.count

        elif search_type == 'communities':
            # Фильтруем сообщества по названию или описанию
            qs = Community.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            ).prefetch_related('posts').order_by('-member_count', 'id')

            paginator = Paginator(qs, 10)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)

            results = page_obj
            total_count = paginator.count

        elif search_type == 'users':
            # Фильтруем пользователей по username
            qs = User.objects.filter(
                username__icontains=query
            ).select_related('profile').prefetch_related('posts', 'comments').order_by('username')

            paginator = Paginator(qs, 10)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)

            # Добавление is_following ПОСЛЕ пагинации
            if request.user.is_authenticated:
                following_ids = set(
                    UserFollow.objects.filter(
                        follower=request.user,
                        following__in=page_obj.object_list
                    ).values_list('following_id', flat=True)
                )
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
    HTMX эндпоинт автодополнения (поисковые подсказки).
    """
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if len(query) >= 2:
        # Поиск по постам (до 5 штук)
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community', 'author')[:5]
        
        # Поиск по сообществам (до 3 штук)
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]
        
        # Поиск по пользователям (до 3 штук)
        users = User.objects.filter(
            username__icontains=query
        )[:3]

        # Форматирование результатов
        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f"c/{post.community.name} • u/{post.author.username}"
            })

        for community in communities:
            suggestions.append({
                'url': reverse('communities:detail', kwargs={'slug': community.slug}),
                'type': 'community',
                'title': f"c/{community.name}",
                'subtitle': f"{community.member_count} участников"
            })

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

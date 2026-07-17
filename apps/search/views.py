from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator
from django.urls import reverse

from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User
from apps.votes.models import PostVote


def search_results(request):
    """Страница результатов поиска."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page_number = request.GET.get('page', 1)
    
    results = []
    total_count = 0

    if query:
        if search_type == 'posts':
            # Поиск по постам: заголовок или текст
            posts_qs = Post.objects.filter(
                is_deleted=False
            ).filter(
                Q(title__icontains=query) | Q(content__icontains=query)
            ).select_related('author', 'community')

            # Prefetch голосов пользователя для предотвращения N+1 запросов
            if request.user.is_authenticated:
                posts_qs = posts_qs.prefetch_related(
                    Prefetch(
                        'votes',
                        queryset=PostVote.objects.filter(user=request.user),
                        to_attr='user_votes'
                    )
                )
            else:
                posts_qs = posts_qs.prefetch_related('votes')

            posts_qs = posts_qs.order_by('-created_at')

            paginator = Paginator(posts_qs, 10)
            page_obj = paginator.get_page(page_number)

            # Заполняем user_vote из предвыборки (Prefetch)
            for post in page_obj:
                if hasattr(post, 'user_votes'):
                    post.user_vote = post.user_votes[0].value if post.user_votes else None
                else:
                    post.user_vote = None

            results = page_obj
            total_count = paginator.count

        elif search_type == 'communities':
            # Поиск по сообществам: название или описание
            communities_qs = Community.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            ).order_by('name')

            paginator = Paginator(communities_qs, 10)
            page_obj = paginator.get_page(page_number)

            results = page_obj
            total_count = paginator.count

        elif search_type == 'users':
            # Поиск по пользователям: имя или био
            users_qs = User.objects.filter(
                Q(username__icontains=query) | Q(profile__bio__icontains=query)
            ).select_related('profile').distinct()

            # Обязательно сортируем queryset во избежание UnorderedObjectListWarning при пагинации
            users_qs = users_qs.order_by('username')

            paginator = Paginator(users_qs, 10)
            page_obj = paginator.get_page(page_number)

            # Проверяем подписки, если пользователь авторизован
            if request.user.is_authenticated:
                from apps.users.models import UserFollow
                following_ids = set(
                    UserFollow.objects.filter(follower=request.user).values_list('following_id', flat=True)
                )
                for u in page_obj:
                    u.is_following = u.id in following_ids
            else:
                for u in page_obj:
                    u.is_following = False

            results = page_obj
            total_count = paginator.count

    return render(request, 'search/results.html', {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
    })


def search_suggestions(request):
    """HTMX эндпоинт автокомплита поиска."""
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
        ).order_by('username')[:3]

        # Форматируем результаты в соответствии со спецификацией
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

        for u in users:
            suggestions.append({
                'url': reverse('users:profile', kwargs={'username': u.username}),
                'type': 'user',
                'title': f"u/{u.username}",
                'subtitle': f"Карма: {u.karma}"
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query,
    })

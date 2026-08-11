from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from django.urls import reverse
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User
from apps.votes.models import PostVote
from apps.users.models import UserFollow


def search_results(request):
    """
    Полностраничные результаты поиска с пагинацией (10 результатов на страницу).
    Поддерживает поиск по постам (posts), сообществам (communities) или пользователям (users).
    Оптимизирует N+1 запросы за счет Prefetch для PostVote.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page_number = request.GET.get('page', 1)

    context = {
        'query': query,
        'search_type': search_type,
        'results': None,
        'total_count': 0,
        'error': None,
    }

    if not query:
        context['error'] = 'Введите поисковый запрос'
        return render(request, 'search/results.html', context)

    if search_type == 'posts':
        queryset = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            is_deleted=False
        ).select_related('author', 'community')

        if request.user.is_authenticated:
            user_votes_prefetch = Prefetch(
                'votes',
                queryset=PostVote.objects.filter(user=request.user),
                to_attr='user_votes_cache'
            )
            queryset = queryset.prefetch_related(user_votes_prefetch)

    elif search_type == 'communities':
        queryset = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        )

    elif search_type == 'users':
        queryset = User.objects.filter(
            username__icontains=query
        ).select_related('profile').order_by('username')

    paginator = Paginator(queryset, 10)
    page_obj = paginator.get_page(page_number)
    
    # Расчет свойств после пагинации
    if search_type == 'posts':
        for post in page_obj.object_list:
            if request.user.is_authenticated:
                votes = getattr(post, 'user_votes_cache', [])
                post.user_vote = votes[0].value if votes else None
            else:
                post.user_vote = None

    elif search_type == 'users' and request.user.is_authenticated:
        user_ids = [u.id for u in page_obj.object_list]
        following_ids = set(
            UserFollow.objects.filter(
                follower=request.user,
                following_id__in=user_ids
            ).values_list('following_id', flat=True)
        )
        for u in page_obj.object_list:
            u.is_following = u.id in following_ids

    context['results'] = page_obj
    context['total_count'] = paginator.count

    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX-эндпоинт для автодополнения (поисковых подсказок).
    """
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if len(query) >= 2:
        # Поиск по постам (до 5 штук)
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

        # Поиск по сообществам (до 3 штук)
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

        # Поиск по пользователям (до 3 штук)
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

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query
    })

from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
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
    """HTMX эндпоинт автокомплита поиска."""
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
            name__icontains=query
        )[:3]
        
        for community in communities:
            suggestions.append({
                'url': reverse('communities:detail', kwargs={'slug': community.slug}),
                'type': 'community',
                'title': f"c/{community.name}",
                'subtitle': f"{community.member_count} участников • {community.description}"
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

    html = render_to_string('search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query
    }, request=request)
    return HttpResponse(html)


def search_results(request):
    """Страница результатов поиска (посты, сообщества или пользователи) с пагинацией."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    results = []
    total_count = 0
    error = None
    
    if query:
        if search_type == 'posts':
            # Оптимизация prefetch_related/select_related для избежания N+1 запросов
            if request.user.is_authenticated:
                post_votes_prefetch = Prefetch(
                    'votes',
                    queryset=PostVote.objects.filter(user=request.user),
                    to_attr='user_vote_cache'
                )
                queryset = Post.objects.filter(
                    title__icontains=query,
                    is_deleted=False
                ).select_related('author', 'community').prefetch_related(post_votes_prefetch).order_by('-created_at')
            else:
                queryset = Post.objects.filter(
                    title__icontains=query,
                    is_deleted=False
                ).select_related('author', 'community').order_by('-created_at')

        elif search_type == 'communities':
            queryset = Community.objects.filter(
                name__icontains=query
            ).order_by('-member_count')

        elif search_type == 'users':
            # Сортировка для Paginator по User модели, чтобы не было warnings
            queryset = User.objects.filter(
                username__icontains=query
            ).select_related('profile').order_by('username')

        # Пагинация: 10 элементов на страницу
        paginator = Paginator(queryset, 10)
        page_number = request.GET.get('page', 1)
        results = paginator.get_page(page_number)
        total_count = paginator.count

        # Пост-обработка результатов
        if search_type == 'posts' and request.user.is_authenticated:
            for post in results:
                cache = getattr(post, 'user_vote_cache', [])
                post.user_vote = cache[0].value if cache else None

        elif search_type == 'users' and request.user.is_authenticated:
            # Оптимально проверяем подписки
            following_ids = set(UserFollow.objects.filter(follower=request.user).values_list('following_id', flat=True))
            for profile_user in results:
                profile_user.is_following = profile_user.id in following_ids
    else:
        error = "Введите поисковый запрос"

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
        'error': error,
    }
    return render(request, 'search/results.html', context)

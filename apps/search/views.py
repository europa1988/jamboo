from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Prefetch

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote
from apps.users.models import UserFollow

User = get_user_model()


def search_results(request):
    """
    Полностраничные результаты поиска с пагинацией (по 10 результатов).
    Поддерживает три вкладки: посты, сообщества, пользователи.
    Оптимизировано prefetch-запросами для голосов авторизованного пользователя.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page_obj = None
    total_count = 0
    error = None

    if not query:
        error = "Введите поисковый запрос"
    else:
        if search_type == 'posts':
            if request.user.is_authenticated:
                results_qs = Post.objects.filter(
                    title__icontains=query,
                    is_deleted=False
                ).select_related('author', 'community').prefetch_related(
                    Prefetch('votes', queryset=PostVote.objects.filter(user=request.user), to_attr='user_votes')
                ).order_by('-created_at')
            else:
                results_qs = Post.objects.filter(
                    title__icontains=query,
                    is_deleted=False
                ).select_related('author', 'community').order_by('-created_at')

        elif search_type == 'communities':
            results_qs = Community.objects.filter(
                name__icontains=query
            ).order_by('-member_count')

        elif search_type == 'users':
            results_qs = User.objects.filter(
                username__icontains=query
            ).select_related('profile').order_by('username')

        paginator = Paginator(results_qs, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        total_count = paginator.count

        # Дополнительная обработка страниц
        if search_type == 'posts':
            if request.user.is_authenticated:
                for post in page_obj:
                    post.user_vote = post.user_votes[0].value if post.user_votes else None
            else:
                for post in page_obj:
                    post.user_vote = None

        elif search_type == 'users':
            if request.user.is_authenticated:
                following_ids = UserFollow.objects.filter(
                    follower=request.user
                ).values_list('following_id', flat=True)
                following_set = set(following_ids)
                for profile_user in page_obj:
                    profile_user.is_following = profile_user.id in following_set
            else:
                for profile_user in page_obj:
                    profile_user.is_following = False

    return render(request, 'search/results.html', {
        'query': query,
        'search_type': search_type,
        'results': page_obj,
        'total_count': total_count,
        'error': error,
    })


def search_suggestions(request):
    """
    HTMX эндпоинт автодополнения (suggestions) поиска.
    Ожидает контекст со списком 'suggestions' (элементы с url, type, title, subtitle).
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
                'subtitle': f'в c/{post.community.name} • автор u/{post.author.username}'
            })

        # Поиск по сообществам (до 3 штук)
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]
        for community in communities:
            suggestions.append({
                'url': reverse('communities:detail', kwargs={'slug': community.slug}),
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников'
            })

        # Поиск по пользователям (до 3 штук)
        users = User.objects.filter(
            username__icontains=query
        ).order_by('username')[:3]
        for user in users:
            suggestions.append({
                'url': reverse('users:profile', kwargs={'username': user.username}),
                'type': 'user',
                'title': f'u/{user.username}',
                'subtitle': f'Карма: {user.karma}'
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query
    })

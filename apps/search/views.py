from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import UserFollow

User = get_user_model()


def search_results(request):
    """
    Основная страница результатов поиска с поддержкой вкладок (посты, сообщества, пользователи) и пагинации.
    """
    q = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    if not q:
        return render(request, 'search/results.html', {
            'query': q,
            'search_type': search_type,
            'error': 'Введите поисковый запрос',
        })

    if len(q) < 2:
        return render(request, 'search/results.html', {
            'query': q,
            'search_type': search_type,
            'error': 'Запрос должен содержать не менее 2 символов',
        })

    page_number = request.GET.get('page', 1)

    if search_type == 'posts':
        qs = Post.objects.filter(is_deleted=False).filter(
            Q(title__icontains=q) | Q(content__icontains=q)
        ).select_related('author', 'community').order_by('-created_at')
        total_count = qs.count()
        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(page_number)

        if request.user.is_authenticated:
            for post in page_obj.object_list:
                post.user_vote = post.get_user_vote(request.user)

    elif search_type == 'communities':
        qs = Community.objects.filter(
            Q(name__icontains=q) | Q(description__icontains=q)
        ).order_by('-member_count')
        total_count = qs.count()
        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(page_number)

    elif search_type == 'users':
        qs = User.objects.filter(
            Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
        ).select_related('profile').order_by('username')
        total_count = qs.count()
        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(page_number)

        if request.user.is_authenticated:
            following_ids = set(
                UserFollow.objects.filter(follower=request.user).values_list('following_id', flat=True)
            )
            for user_obj in page_obj.object_list:
                user_obj.is_following = user_obj.id in following_ids

    context = {
        'query': q,
        'search_type': search_type,
        'results': page_obj,
        'total_count': total_count,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX эндпоинт выпадающих подсказок для поисковой строки.
    """
    q = request.GET.get('q', '').strip()
    suggestions = []

    if len(q) >= 2:
        # Поиск по постам (до 5)
        posts = Post.objects.filter(
            title__icontains=q,
            is_deleted=False
        ).select_related('community', 'author')[:5]

        for post in posts:
            suggestions.append({
                'title': post.title,
                'subtitle': f'c/{post.community.name} • u/{post.author.username}',
                'url': post.get_absolute_url(),
                'type': 'post',
            })

        # Поиск по сообществам (до 3)
        communities = Community.objects.filter(
            name__icontains=q
        )[:3]

        for community in communities:
            suggestions.append({
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
                'url': community.get_absolute_url(),
                'type': 'community',
            })

        # Поиск по пользователям (до 3)
        users = User.objects.filter(
            username__icontains=q
        )[:3]

        for user_obj in users:
            suggestions.append({
                'title': f'u/{user_obj.username}',
                'subtitle': f'Карма: {user_obj.karma}',
                'url': user_obj.get_absolute_url(),
                'type': 'user',
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': q,
    })

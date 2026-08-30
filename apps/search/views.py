from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User
from apps.votes.models import PostVote


def search_results(request):
    """Страница результатов поиска с пагинацией (посты, сообщества, пользователи)."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ('posts', 'communities', 'users'):
        search_type = 'posts'

    error = None
    page_obj = None
    total_count = 0

    if not query:
        error = "Введите поисковый запрос"
    elif len(query) < 2:
        error = "Запрос должен содержать минимум 2 символа"
    else:
        if search_type == 'posts':
            posts_qs = Post.objects.filter(
                title__icontains=query,
                is_deleted=False
            ).select_related('author', 'community').order_by('-created_at')

            if request.user.is_authenticated:
                user_votes = PostVote.objects.filter(user=request.user)
                posts_qs = posts_qs.prefetch_related(
                    Prefetch('votes', queryset=user_votes, to_attr='user_votes')
                )

            paginator = Paginator(posts_qs, 10)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            total_count = paginator.count

        elif search_type == 'communities':
            communities_qs = Community.objects.filter(
                name__icontains=query,
                is_active=True
            ).order_by('-created_at')

            paginator = Paginator(communities_qs, 10)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            total_count = paginator.count

        elif search_type == 'users':
            users_qs = User.objects.filter(
                username__icontains=query,
                is_active=True
            ).order_by('-date_joined')

            paginator = Paginator(users_qs, 10)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            total_count = paginator.count

    context = {
        'query': query,
        'search_type': search_type,
        'error': error,
        'page_obj': page_obj,
        'results': page_obj,
        'total_count': total_count,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """HTMX эндпоинт подсказок для поиска."""
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # Посты
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('author', 'community').order_by('-created_at')[:3]

        for p in posts:
            suggestions.append({
                'url': p.get_absolute_url(),
                'type': 'post',
                'title': p.title,
                'subtitle': f"в {p.community.name if p.community else 'личных'}",
            })

        # Сообщества
        communities = Community.objects.filter(
            name__icontains=query,
            is_active=True
        ).order_by('-created_at')[:3]

        for c in communities:
            suggestions.append({
                'url': c.get_absolute_url(),
                'type': 'community',
                'title': c.name,
                'subtitle': f"{c.member_count} участников",
            })

        # Пользователи
        users = User.objects.filter(
            username__icontains=query,
            is_active=True
        ).select_related('profile').order_by('-date_joined')[:3]

        for u in users:
            bio = u.profile.bio if hasattr(u, 'profile') and u.profile and u.profile.bio else "Пользователь"
            suggestions.append({
                'url': u.get_absolute_url(),
                'type': 'user',
                'title': u.username,
                'subtitle': bio[:30],
            })

    context = {
        'query': query,
        'suggestions': suggestions,
    }
    return render(request, 'search/partials/suggestions.html', context)

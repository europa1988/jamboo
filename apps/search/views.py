from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote

User = get_user_model()


def search_results(request):
    """Отображение результатов поиска с пагинацией (10 элементов на страницу)."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')

    if search_type not in ('posts', 'communities', 'users'):
        search_type = 'posts'

    page_number = request.GET.get('page', 1)
    page_obj = None
    total_count = 0
    error = None

    if not query:
        error = "Введите поисковый запрос"
    elif len(query) < 2:
        error = "Запрос должен содержать минимум 2 символа"
    else:
        if search_type == 'posts':
            posts_qs = Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                is_deleted=False
            ).select_related('author', 'community').order_by('-created_at')

            if request.user.is_authenticated:
                user_votes = PostVote.objects.filter(user=request.user)
                posts_qs = posts_qs.prefetch_related(
                    Prefetch('user_vote', queryset=user_votes, to_attr='user_vote_cache')
                )

            paginator = Paginator(posts_qs, 10)
            page_obj = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                for post in page_obj.object_list:
                    votes = getattr(post, 'user_vote_cache', [])
                    post.user_vote = votes[0].value if votes else 0

        elif search_type == 'communities':
            communities_qs = Community.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            ).order_by('-member_count')

            paginator = Paginator(communities_qs, 10)
            page_obj = paginator.get_page(page_number)
            total_count = paginator.count

        elif search_type == 'users':
            users_qs = User.objects.filter(
                Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
            ).order_by('username')

            paginator = Paginator(users_qs, 10)
            page_obj = paginator.get_page(page_number)
            total_count = paginator.count

    context = {
        'query': query,
        'search_type': search_type,
        'page_obj': page_obj,
        'total_count': total_count,
        'error': error,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """HTMX эндпоинт автокомплита поиска."""
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # Посты
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community')[:3]
        for p in posts:
            suggestions.append({
                'title': p.title,
                'subtitle': f'в r/{p.community.slug}' if p.community else 'Пост',
                'url': p.get_absolute_url(),
                'type': 'post'
            })

        # Сообщества
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]
        for c in communities:
            suggestions.append({
                'title': c.name,
                'subtitle': f'{c.member_count} участников',
                'url': c.get_absolute_url(),
                'type': 'community'
            })

        # Пользователи
        users = User.objects.filter(
            username__icontains=query
        )[:3]
        for u in users:
            suggestions.append({
                'title': u.username,
                'subtitle': 'Пользователь',
                'url': u.get_absolute_url(),
                'type': 'user'
            })

    return render(request, 'search/partials/suggestions.html', {'suggestions': suggestions, 'query': query})

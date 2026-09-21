from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.contrib.auth import get_user_model
from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote

User = get_user_model()


def search_results(request):
    """
    Страница результатов поиска (посты, сообщества, пользователи).
    поддерживает пагинацию (10 элементов на страницу) и Prefetch для PostVote.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ('posts', 'communities', 'users'):
        search_type = 'posts'

    error = None
    page_obj = None
    total_count = 0

    if query:
        if len(query) < 2:
            error = "Поисковый запрос должен содержать минимум 2 символа."
        else:
            if search_type == 'posts':
                queryset = Post.objects.filter(
                    title__icontains=query,
                    is_deleted=False
                ).select_related('author', 'community').order_by('-created_at')

                if request.user.is_authenticated:
                    queryset = queryset.prefetch_related(
                        Prefetch(
                            'votes',
                            queryset=PostVote.objects.filter(user=request.user),
                            to_attr='user_vote'
                        )
                    )

            elif search_type == 'communities':
                queryset = Community.objects.filter(
                    name__icontains=query,
                    is_active=True
                ).order_by('-created_at')

            elif search_type == 'users':
                queryset = User.objects.filter(
                    username__icontains=query,
                    is_active=True
                ).order_by('username')

            paginator = Paginator(queryset, 10)
            page_number = request.GET.get('page')
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
    """
    HTMX эндпоинт автокомплита поиска.
    Возвращает список `suggestions` с элементами url, type, title, subtitle.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # Посты
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community', 'author')[:3]
        for p in posts:
            suggestions.append({
                'url': p.get_absolute_url(),
                'type': 'post',
                'title': p.title,
                'subtitle': f"в r/{p.community.slug}" if p.community else "автор " + p.author.username
            })

        # Сообщества
        communities = Community.objects.filter(
            name__icontains=query,
            is_active=True
        )[:3]
        for c in communities:
            suggestions.append({
                'url': c.get_absolute_url(),
                'type': 'community',
                'title': f"r/{c.name}",
                'subtitle': f"{c.member_count} участников"
            })

        # Пользователи
        users = User.objects.filter(
            username__icontains=query,
            is_active=True
        )[:3]
        for u in users:
            suggestions.append({
                'url': u.get_absolute_url(),
                'type': 'user',
                'title': f"u/{u.username}",
                'subtitle': u.get_full_name() or u.username
            })

    context = {
        'query': query,
        'suggestions': suggestions,
    }
    return render(request, 'search/partials/suggestions.html', context)

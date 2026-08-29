from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User
from apps.votes.models import PostVote


def search_results(request):
    """
    Страница результатов поиска с фильтрацией и пагинацией.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    page_number = request.GET.get('page', 1)

    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    context = {
        'query': query,
        'search_type': search_type,
        'page_obj': None,
        'total_count': 0,
        'error': None,
    }

    if not query:
        return render(request, 'search/results.html', context)

    if search_type == 'posts':
        qs = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            is_deleted=False
        ).select_related('author', 'community').order_by('-created_at')

        if request.user.is_authenticated:
            qs = qs.prefetch_related(
                Prefetch(
                    'votes',
                    queryset=PostVote.objects.filter(user=request.user),
                    to_attr='user_votes'
                )
            )

        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(page_number)

        if request.user.is_authenticated:
            for post in page_obj:
                post.user_vote = post.user_votes[0].value if getattr(post, 'user_votes', []) else 0

        context['page_obj'] = page_obj
        context['total_count'] = paginator.count

    elif search_type == 'communities':
        qs = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).order_by('-member_count')

        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        context['total_count'] = paginator.count

    elif search_type == 'users':
        qs = User.objects.filter(
            Q(username__icontains=query) | Q(profile__bio__icontains=query)
        ).order_by('username')

        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        context['total_count'] = paginator.count

    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX эндпоинт для выпадающих подсказок автодополнения.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # Посты
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community')[:3]

        for post in posts:
            suggestions.append({
                'title': post.title,
                'subtitle': f'c/{post.community.name}' if post.community else 'Пост',
                'url': post.get_absolute_url(),
                'type': 'post'
            })

        # Сообщества
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]

        for community in communities:
            suggestions.append({
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
                'url': community.get_absolute_url(),
                'type': 'community'
            })

        # Пользователи
        users = User.objects.filter(
            username__icontains=query
        )[:3]

        for user in users:
            suggestions.append({
                'title': f'u/{user.username}',
                'subtitle': user.profile.bio[:40] if hasattr(user, 'profile') and user.profile.bio else 'Пользователь',
                'url': user.get_absolute_url(),
                'type': 'user'
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query
    })

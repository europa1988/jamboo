from django.shortcuts import render
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.db.models import Q, Prefetch
from django.http import HttpResponse
from django.template.loader import render_to_string

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote
from apps.users.models import UserFollow

User = get_user_model()


def search_results(request):
    """Страница результатов поиска с пагинацией и выбором категорий (посты, сообщества, пользователи)."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page = request.GET.get('page', 1)
    error = None
    results = []
    total_count = 0

    if query:
        if search_type == 'posts':
            queryset = Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                is_deleted=False
            ).select_related('author', 'community').order_by('-created_at')

            if request.user.is_authenticated:
                user_votes = PostVote.objects.filter(user=request.user)
                queryset = queryset.prefetch_related(
                    Prefetch('votes', queryset=user_votes, to_attr='current_user_votes')
                )

            paginator = Paginator(queryset, 10)
            results = paginator.get_page(page)
            total_count = paginator.count

            if request.user.is_authenticated:
                for post in results:
                    post.user_vote = post.current_user_votes[0].value if getattr(post, 'current_user_votes', []) else None
            else:
                for post in results:
                    post.user_vote = None

        elif search_type == 'communities':
            queryset = Community.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            ).order_by('-member_count')

            paginator = Paginator(queryset, 10)
            results = paginator.get_page(page)
            total_count = paginator.count

        elif search_type == 'users':
            queryset = User.objects.filter(
                Q(username__icontains=query) | Q(profile__bio__icontains=query)
            ).select_related('profile').order_by('id')

            paginator = Paginator(queryset, 10)
            results = paginator.get_page(page)
            total_count = paginator.count

            if request.user.is_authenticated:
                following_ids = set(
                    UserFollow.objects.filter(follower=request.user).values_list('following_id', flat=True)
                )
                for profile_user in results:
                    profile_user.is_following = profile_user.id in following_ids
            else:
                for profile_user in results:
                    profile_user.is_following = False

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
        'error': error,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """HTMX эндпоинт подсказок поиска."""
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # Посты
        posts = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            is_deleted=False
        ).select_related('community')[:3]

        for post in posts:
            suggestions.append({
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}',
                'url': post.get_absolute_url()
            })

        # Сообщества
        communities = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )[:3]

        for community in communities:
            suggestions.append({
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
                'url': f'/c/{community.slug}/'
            })

        # Пользователи
        users = User.objects.filter(
            Q(username__icontains=query)
        )[:3]

        for u in users:
            suggestions.append({
                'type': 'user',
                'title': f'u/{u.username}',
                'subtitle': f'Карма: {u.karma}',
                'url': f'/u/{u.username}/'
            })

    html = render_to_string('search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query,
    }, request=request)
    return HttpResponse(html)

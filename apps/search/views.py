from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow


def search_results(request):
    """Страница результатов поиска с вкладками и пагинацией."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    results = []
    total_count = 0

    if query:
        if search_type == 'posts':
            queryset = Post.objects.filter(
                is_deleted=False
            ).filter(
                Q(title__icontains=query) | Q(content__icontains=query)
            ).select_related('author', 'community').prefetch_related('votes').order_by('-created_at')

            paginator = Paginator(queryset, 10)
            page_number = request.GET.get('page')
            results = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                for post in results:
                    post.user_vote = post.get_user_vote(request.user)

        elif search_type == 'communities':
            queryset = Community.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            ).order_by('-member_count')

            paginator = Paginator(queryset, 10)
            page_number = request.GET.get('page')
            results = paginator.get_page(page_number)
            total_count = paginator.count

        elif search_type == 'users':
            queryset = User.objects.filter(
                Q(username__icontains=query) | Q(profile__bio__icontains=query)
            ).order_by('username')

            paginator = Paginator(queryset, 10)
            page_number = request.GET.get('page')
            results = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                following_ids = set(
                    UserFollow.objects.filter(follower=request.user).values_list('following_id', flat=True)
                )
                for u in results:
                    u.is_following = u.id in following_ids

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """HTMX автокомплит для поиска."""
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # Посты
        posts = Post.objects.filter(
            is_deleted=False
        ).filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        ).select_related('community')[:3]

        for post in posts:
            suggestions.append({
                'type': 'post',
                'title': post.title,
                'subtitle': f"c/{post.community.name}",
                'url': post.get_absolute_url(),
            })

        # Сообщества
        communities = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )[:3]

        for community in communities:
            suggestions.append({
                'type': 'community',
                'title': f"c/{community.name}",
                'subtitle': f"{community.member_count} участников",
                'url': community.get_absolute_url(),
            })

        # Пользователи
        users = User.objects.filter(
            Q(username__icontains=query) | Q(profile__bio__icontains=query)
        ).order_by('username')[:3]

        for u in users:
            suggestions.append({
                'type': 'user',
                'title': f"u/{u.username}",
                'subtitle': f"Карма: {u.karma}",
                'url': u.get_absolute_url(),
            })

    context = {
        'suggestions': suggestions,
        'query': query,
    }
    return render(request, 'search/partials/suggestions.html', context)

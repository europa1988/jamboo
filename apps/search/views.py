from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User
from apps.votes.models import PostVote


def search_results(request):
    """
    Основная страница поиска с вкладками (посты, сообщества, пользователи) и пагинацией.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    error = None
    results_page = None
    total_count = 0

    if query:
        if search_type == 'posts':
            posts_qs = Post.objects.filter(
                title__icontains=query,
                is_deleted=False
            ).select_related('author', 'community')

            if request.user.is_authenticated:
                user_votes = PostVote.objects.filter(user=request.user)
                posts_qs = posts_qs.prefetch_related(
                    Prefetch('votes', queryset=user_votes, to_attr='user_votes')
                )

            paginator = Paginator(posts_qs, 10)
            page_number = request.GET.get('page', 1)
            results_page = paginator.get_page(page_number)
            total_count = paginator.count

        elif search_type == 'communities':
            communities_qs = Community.objects.filter(
                name__icontains=query
            )
            paginator = Paginator(communities_qs, 10)
            page_number = request.GET.get('page', 1)
            results_page = paginator.get_page(page_number)
            total_count = paginator.count

        elif search_type == 'users':
            users_qs = User.objects.filter(
                username__icontains=query
            ).order_by('username')
            paginator = Paginator(users_qs, 10)
            page_number = request.GET.get('page', 1)
            results_page = paginator.get_page(page_number)
            total_count = paginator.count

    context = {
        'query': query,
        'search_type': search_type,
        'results': results_page,
        'total_count': total_count,
        'error': error,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX эндпоинт автокомплита поиска.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community')[:3]

        for post in posts:
            suggestions.append({
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}',
                'url': post.get_absolute_url()
            })

        communities = Community.objects.filter(
            name__icontains=query
        )[:3]

        for community in communities:
            suggestions.append({
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
                'url': community.get_absolute_url() if hasattr(community, 'get_absolute_url') else f'/c/{community.slug}/'
            })

        users = User.objects.filter(
            username__icontains=query
        )[:3]

        for user in users:
            suggestions.append({
                'type': 'user',
                'title': f'u/{user.username}',
                'subtitle': f'Карма: {user.karma}',
                'url': user.get_absolute_url() if hasattr(user, 'get_absolute_url') else f'/u/{user.username}/'
            })

    context = {
        'suggestions': suggestions,
        'query': query,
    }
    return render(request, 'search/partials/suggestions.html', context)

from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.urls import reverse

from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_results(request):
    """
    Основное представление результатов поиска по постам, сообществам и пользователям.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    page_number = request.GET.get('page', 1)
    
    context = {
        'query': query,
        'search_type': search_type,
        'results': None,
        'total_count': 0,
        'error': None,
    }

    if not query:
        return render(request, 'search/results.html', context)

    if search_type == 'posts':
        queryset = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('author', 'community').order_by('-created_at')

        if request.user.is_authenticated:
            user_votes = PostVote.objects.filter(user=request.user)
            queryset = queryset.prefetch_related(
                Prefetch('votes', queryset=user_votes, to_attr='current_user_votes')
            )

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)

        if request.user.is_authenticated:
            for post in page_obj:
                votes = getattr(post, 'current_user_votes', [])
                post.user_vote = votes[0].value if votes else None

        context['results'] = page_obj
        context['total_count'] = paginator.count

    elif search_type == 'communities':
        queryset = Community.objects.filter(
            name__icontains=query
        ).order_by('-member_count')

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)

        context['results'] = page_obj
        context['total_count'] = paginator.count

    elif search_type == 'users':
        queryset = User.objects.filter(
            username__icontains=query
        ).select_related('profile').order_by('username')

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)

        if request.user.is_authenticated:
            user_ids = [u.id for u in page_obj]
            following_ids = set(
                UserFollow.objects.filter(
                    follower=request.user,
                    following_id__in=user_ids
                ).values_list('following_id', flat=True)
            )
            for u in page_obj:
                u.is_following = u.id in following_ids

        context['results'] = page_obj
        context['total_count'] = paginator.count

    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX эндпоинт для автодополнения/подсказок поиска.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community')[:3]
        for p in posts:
            suggestions.append({
                'type': 'post',
                'title': p.title,
                'subtitle': f"c/{p.community.name}",
                'url': p.get_absolute_url(),
            })

        communities = Community.objects.filter(
            name__icontains=query
        )[:3]
        for c in communities:
            suggestions.append({
                'type': 'community',
                'title': f"c/{c.name}",
                'subtitle': f"{c.member_count} участников",
                'url': reverse('communities:detail', kwargs={'slug': c.slug}),
            })

        users = User.objects.filter(
            username__icontains=query
        )[:3]
        for u in users:
            suggestions.append({
                'type': 'user',
                'title': f"u/{u.username}",
                'subtitle': f"Карма: {u.karma}",
                'url': reverse('users:profile', kwargs={'username': u.username}),
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query,
    })

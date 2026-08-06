from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse

from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_results(request):
    """
    Полностраничные результаты поиска с пагинацией (10 результатов на страницу).
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts').strip()
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    results = []
    total_count = 0
    error = None

    if query:
        if search_type == 'posts':
            posts = Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                is_deleted=False
            ).select_related('author', 'community')

            # Utilizes 'Prefetch' for 'PostVote' objects to optimize performance for authenticated users.
            if request.user.is_authenticated:
                user_votes = PostVote.objects.filter(user=request.user)
                posts = posts.prefetch_related(
                    Prefetch('votes', queryset=user_votes, to_attr='user_votes_cache')
                )

            # Django querysets used with the Paginator must include an explicit 'order_by' clause.
            posts = posts.order_by('-created_at')
            total_count = posts.count()

            # Pagination occurs first so that queryset evaluation/slicing does not discard these custom attributes
            paginator = Paginator(posts, 10)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)

            if request.user.is_authenticated:
                for post in page_obj:
                    post.user_vote = post.get_user_vote(request.user)

            results = page_obj

        elif search_type == 'communities':
            communities = Community.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            ).order_by('-member_count')
            total_count = communities.count()

            paginator = Paginator(communities, 10)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            results = page_obj

        elif search_type == 'users':
            users = User.objects.filter(
                username__icontains=query
            ).select_related('profile').order_by('username')

            total_count = users.count()

            paginator = Paginator(users, 10)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)

            if request.user.is_authenticated:
                for profile_user in page_obj:
                    profile_user.is_following = UserFollow.objects.filter(
                        follower=request.user,
                        following=profile_user
                    ).exists()
            results = page_obj

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
        'error': error
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX эндпоинт автокомплита поиска.
    Возвращает список подсказок, где каждый элемент содержит keys: 'url', 'type', 'title', 'subtitle'.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if len(query) >= 2:
        # Поиск по постам
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('author', 'community')[:5]
        
        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f"c/{post.community.name} • Автор: u/{post.author.username}"
            })

        # Поиск по сообществам
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]
        
        for community in communities:
            suggestions.append({
                'url': reverse('communities:detail', kwargs={'slug': community.slug}),
                'type': 'community',
                'title': f"c/{community.name}",
                'subtitle': f"{community.member_count} участников"
            })

        # Поиск по пользователям
        users = User.objects.filter(
            username__icontains=query
        )[:3]

        for profile_user in users:
            suggestions.append({
                'url': reverse('users:profile', kwargs={'username': profile_user.username}),
                'type': 'user',
                'title': f"u/{profile_user.username}",
                'subtitle': f"Карма: {profile_user.karma}"
            })

    context = {
        'suggestions': suggestions,
        'query': query,
    }
    return render(request, 'search/partials/suggestions.html', context)

from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.http import HttpResponse
from django.template.loader import render_to_string

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote

User = get_user_model()


def search_results(request):
    """
    Полностраничный поиск с пагинацией.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts').strip()
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page_number = request.GET.get('page', '1')
    results = []
    total_count = 0
    error = None

    if query:
        if search_type == 'posts':
            # "The 'search_results' view implements pagination with 10 results per page and utilizes 'Prefetch' for 'PostVote' objects to optimize performance for authenticated users."
            posts_qs = Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                is_deleted=False
            ).select_related('author', 'community')

            if request.user.is_authenticated:
                posts_qs = posts_qs.prefetch_related(
                    Prefetch(
                        'votes',
                        queryset=PostVote.objects.filter(user=request.user),
                        to_attr='user_votes'
                    )
                )

            posts_qs = posts_qs.order_by('-created_at')

            paginator = Paginator(posts_qs, 10)
            page_obj = paginator.get_page(page_number)
            results = page_obj
            total_count = paginator.count

            if request.user.is_authenticated:
                for post in results:
                    post.user_vote = post.user_votes[0].value if post.user_votes else None

        elif search_type == 'communities':
            communities_qs = Community.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            ).order_by('-member_count')

            paginator = Paginator(communities_qs, 10)
            page_obj = paginator.get_page(page_number)
            results = page_obj
            total_count = paginator.count

        elif search_type == 'users':
            # "Django querysets used with the Paginator (specifically the User model) must include an explicit 'order_by' clause to ensure consistent results and avoid 'UnorderedObjectListWarning'."
            users_qs = User.objects.filter(
                Q(username__icontains=query) | Q(profile__bio__icontains=query)
            ).select_related('profile').order_by('username')

            # Check subscriptions
            if request.user.is_authenticated:
                from apps.users.models import UserFollow
                followed_ids = set(
                    UserFollow.objects.filter(follower=request.user).values_list('following_id', flat=True)
                )

                paginator = Paginator(users_qs, 10)
                page_obj = paginator.get_page(page_number)
                results = page_obj
                total_count = paginator.count

                for profile_user in results:
                    profile_user.is_following = profile_user.id in followed_ids
            else:
                paginator = Paginator(users_qs, 10)
                page_obj = paginator.get_page(page_number)
                results = page_obj
                total_count = paginator.count
    else:
        results = None
        total_count = 0

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
        'error': error,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX-эндпоинт автодополнения для поиска.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if len(query) >= 2:
        # 1. Поиск по постам (до 5 штук)
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community', 'author')[:5]
        
        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f"c/{post.community.name} • u/{post.author.username}"
            })

        # 2. Поиск по сообществам (до 3 штук)
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

        # 3. Поиск по пользователям (до 3 штук)
        users = User.objects.filter(
            username__icontains=query
        ).select_related('profile')[:3]

        for user in users:
            subtitle = user.profile.bio if (hasattr(user, 'profile') and user.profile.bio) else f"Карма: {user.karma}"
            suggestions.append({
                'url': reverse('users:profile', kwargs={'username': user.username}),
                'type': 'user',
                'title': f"u/{user.username}",
                'subtitle': subtitle
            })

    context = {
        'suggestions': suggestions,
        'query': query
    }
    html = render_to_string('search/partials/suggestions.html', context, request=request)
    return HttpResponse(html)

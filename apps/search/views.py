from django.shortcuts import render
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_suggestions(request):
    """
    HTMX endpoint for autocomplete search suggestions.
    Expects context with a 'suggestions' list of items, where each item must contain:
    - 'url'
    - 'type' ('post', 'community', or 'user')
    - 'title'
    - 'subtitle'
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # Search posts (up to 5)
        posts = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            is_deleted=False
        ).select_related('community', 'author')[:5]

        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f"c/{post.community.name} • u/{post.author.username}"
            })

        # Search communities (up to 3)
        communities = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )[:3]

        for c in communities:
            suggestions.append({
                'url': reverse('communities:detail', kwargs={'slug': c.slug}),
                'type': 'community',
                'title': f"c/{c.name}",
                'subtitle': f"{c.member_count} участников"
            })

        # Search users (up to 3)
        users = User.objects.filter(
            Q(username__icontains=query) | Q(profile__bio__icontains=query)
        ).select_related('profile')[:3]

        for u in users:
            suggestions.append({
                'url': reverse('users:profile', kwargs={'username': u.username}),
                'type': 'user',
                'title': f"u/{u.username}",
                'subtitle': f"Карма: {u.karma}"
            })

    # Render HTMX suggestions partial using standard render helper to allow template context inspection in tests
    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query
    })


def search_results(request):
    """
    Full-page search results with pagination.
    Supports search types: 'posts', 'communities', 'users'.
    Paginates by 10 results per page.
    For 'posts', optimizes with Prefetch for authenticated users.
    For 'users', includes is_following status and explicit order_by.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts').strip()
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    if not query:
        queryset = Post.objects.none()
    else:
        if search_type == 'posts':
            queryset = Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                is_deleted=False
            ).select_related('author', 'community').order_by('-created_at')

            if request.user.is_authenticated:
                queryset = queryset.prefetch_related(
                    Prefetch('votes', queryset=PostVote.objects.filter(user=request.user), to_attr='user_votes')
                )

        elif search_type == 'communities':
            queryset = Community.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            ).order_by('-member_count', 'id')

        elif search_type == 'users':
            queryset = User.objects.filter(
                Q(username__icontains=query) | Q(profile__bio__icontains=query)
            ).select_related('profile').order_by('username')

    # Paginate first
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # Set python-level pre-calculated attributes on paginated instances
    if query:
        if search_type == 'posts':
            if request.user.is_authenticated:
                for post in page_obj.object_list:
                    post.user_vote = post.user_votes[0].value if hasattr(post, 'user_votes') and post.user_votes else None
            else:
                for post in page_obj.object_list:
                    post.user_vote = None

        elif search_type == 'users':
            if request.user.is_authenticated:
                following_ids = set(UserFollow.objects.filter(follower=request.user).values_list('following_id', flat=True))
                for profile_user in page_obj.object_list:
                    profile_user.is_following = profile_user.id in following_ids
            else:
                for profile_user in page_obj.object_list:
                    profile_user.is_following = False

    context = {
        'query': query,
        'search_type': search_type,
        'results': page_obj,
        'total_count': paginator.count,
    }

    return render(request, 'search/results.html', context)

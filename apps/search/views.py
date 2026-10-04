from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Prefetch
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User
from apps.votes.models import PostVote


def search_results(request):
    """Страница результатов поиска."""
    query = request.GET.get('q', '').strip()
    tab = request.GET.get('tab', 'posts')
    page_number = request.GET.get('page', 1)

    posts = []
    communities = []
    users = []
    page_obj = None

    if query:
        if tab == 'communities':
            communities_list = Community.objects.filter(
                name__icontains=query,
                is_active=True
            ).order_by('-member_count')
            paginator = Paginator(communities_list, 10)
            page_obj = paginator.get_page(page_number)
            communities = page_obj
        elif tab == 'users':
            users_list = User.objects.filter(
                username__icontains=query,
                is_active=True
            ).order_by('username')
            paginator = Paginator(users_list, 10)
            page_obj = paginator.get_page(page_number)
            users = page_obj
        else:
            # default: posts
            tab = 'posts'
            posts_list = Post.objects.filter(
                title__icontains=query,
                is_deleted=False
            ).select_related('author', 'community').order_by('-created_at')

            if request.user.is_authenticated:
                user_votes = PostVote.objects.filter(user=request.user)
                posts_list = posts_list.prefetch_related(
                    Prefetch('votes', queryset=user_votes, to_attr='current_user_votes')
                )

            paginator = Paginator(posts_list, 10)
            page_obj = paginator.get_page(page_number)
            posts = page_obj

            if request.user.is_authenticated:
                for post in posts:
                    votes = getattr(post, 'current_user_votes', [])
                    post.user_vote = votes[0].value if votes else 0

    context = {
        'query': query,
        'tab': tab,
        'posts': posts,
        'communities': communities,
        'users': users,
        'page_obj': page_obj,
    }

    if request.headers.get('HX-Request'):
        if tab == 'communities':
            template_name = 'search/partials/community_results.html'
        elif tab == 'users':
            template_name = 'search/partials/user_results.html'
        else:
            template_name = 'search/partials/post_results.html'
        return render(request, template_name, context)

    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """HTMX эндпоинт автокомплита поиска."""
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community')[:5]

        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f"в c/{post.community.slug}" if post.community else ""
            })

        communities = Community.objects.filter(
            name__icontains=query,
            is_active=True
        )[:3]

        for community in communities:
            suggestions.append({
                'url': community.get_absolute_url(),
                'type': 'community',
                'title': community.name,
                'subtitle': f"c/{community.slug}"
            })

        users = User.objects.filter(
            username__icontains=query,
            is_active=True
        )[:3]

        for user in users:
            suggestions.append({
                'url': user.get_absolute_url(),
                'type': 'user',
                'title': user.username,
                'subtitle': f"u/{user.username}"
            })

    context = {'suggestions': suggestions, 'query': query}
    return render(request, 'search/partials/suggestions.html', context)

from django.shortcuts import render
from django.core.paginator import Paginator
from django.urls import reverse
from django.db.models import Prefetch
from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote
from django.contrib.auth import get_user_model

User = get_user_model()


def search_results(request):
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts').strip()
    
    results = []
    total_count = 0
    error = None

    if not query:
        return render(request, 'search/results.html', {
            'query': query,
            'search_type': search_type,
            'results': results,
            'total_count': total_count,
            'error': error
        })

    try:
        if search_type == 'posts':
            posts_qs = Post.objects.filter(
                title__icontains=query,
                is_deleted=False
            ).select_related('author', 'community')

            if request.user.is_authenticated:
                posts_qs = posts_qs.prefetch_related(
                    Prefetch(
                        'votes',
                        queryset=PostVote.objects.filter(user=request.user),
                        to_attr='user_votes_list'
                    )
                )
            posts_qs = posts_qs.order_by('-created_at')

            paginator = Paginator(posts_qs, 10)
            page_number = request.GET.get('page')
            results = paginator.get_page(page_number)
            total_count = paginator.count

            for post in results:
                if request.user.is_authenticated and hasattr(post, 'user_votes_list') and post.user_votes_list:
                    post.user_vote = post.user_votes_list[0].value
                else:
                    post.user_vote = None

        elif search_type == 'communities':
            communities_qs = Community.objects.filter(
                name__icontains=query,
                is_active=True
            ).order_by('-member_count')

            paginator = Paginator(communities_qs, 10)
            page_number = request.GET.get('page')
            results = paginator.get_page(page_number)
            total_count = paginator.count

        elif search_type == 'users':
            users_qs = User.objects.filter(
                username__icontains=query,
                is_active=True
            ).order_by('username')

            paginator = Paginator(users_qs, 10)
            page_number = request.GET.get('page')
            results = paginator.get_page(page_number)
            total_count = paginator.count

            # Check if current user is following the user in results
            if request.user.is_authenticated:
                followed_user_ids = set(
                    request.user.following.values_list('following_id', flat=True)
                )
                for u in results:
                    u.is_following = u.id in followed_user_ids
            else:
                for u in results:
                    u.is_following = False
        else:
            error = f"Неизвестный тип поиска: {search_type}"

    except Exception as e:
        error = f"Произошла ошибка при поиске: {str(e)}"

    return render(request, 'search/results.html', {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
        'error': error
    })


def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if len(query) >= 2:
        # Posts
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community')[:5]
        for p in posts:
            suggestions.append({
                'url': p.get_absolute_url(),
                'type': 'post',
                'title': p.title,
                'subtitle': f"c/{p.community.name}",
            })

        # Communities
        communities = Community.objects.filter(
            name__icontains=query,
            is_active=True
        )[:3]
        for c in communities:
            suggestions.append({
                'url': reverse('communities:detail', kwargs={'slug': c.slug}),
                'type': 'community',
                'title': f"c/{c.name}",
                'subtitle': f"{c.member_count} участников",
            })

        # Users
        users = User.objects.filter(
            username__icontains=query,
            is_active=True
        )[:3]
        for u in users:
            suggestions.append({
                'url': reverse('users:profile', kwargs={'username': u.username}),
                'type': 'user',
                'title': f"u/{u.username}",
                'subtitle': f"Карма: {u.karma}",
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query
    })

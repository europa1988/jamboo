from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote

User = get_user_model()


def search_results(request):
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page_num = request.GET.get('page', 1)

    if not query:
        context = {
            'query': '',
            'search_type': search_type,
            'results': None,
            'total_count': 0,
            'error': 'Введите поисковый запрос'
        }
        return render(request, 'search/results.html', context)

    if search_type == 'posts':
        qs = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            is_deleted=False
        ).select_related('author', 'community').order_by('-created_at')

        if request.user.is_authenticated:
            qs = qs.prefetch_related(
                Prefetch('votes', queryset=PostVote.objects.filter(user=request.user))
            )

        paginator = Paginator(qs, 10)
        results = paginator.get_page(page_num)

        if request.user.is_authenticated:
            for post in results:
                post.user_vote = post.get_user_vote(request.user)

    elif search_type == 'communities':
        qs = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).order_by('-member_count', 'name')

        paginator = Paginator(qs, 10)
        results = paginator.get_page(page_num)

    elif search_type == 'users':
        qs = User.objects.filter(
            Q(username__icontains=query) | Q(profile__bio__icontains=query)
        ).select_related('profile').order_by('username')

        paginator = Paginator(qs, 10)
        results = paginator.get_page(page_num)

        if request.user.is_authenticated:
            following_ids = set(request.user.following.values_list('following_id', flat=True))
            for u in results:
                u.is_following = u.id in following_ids

    total_count = paginator.count

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        posts = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            is_deleted=False
        ).select_related('community')[:3]
        for p in posts:
            suggestions.append({
                'type': 'post',
                'title': p.title,
                'subtitle': f"c/{p.community.name}",
                'url': p.get_absolute_url()
            })

        communities = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )[:3]
        for c in communities:
            suggestions.append({
                'type': 'community',
                'title': f"c/{c.name}",
                'subtitle': f"{c.member_count} участников",
                'url': c.get_absolute_url()
            })

        users = User.objects.filter(
            username__icontains=query
        )[:3]
        for u in users:
            suggestions.append({
                'type': 'user',
                'title': f"u/{u.username}",
                'subtitle': f"Карма: {getattr(u, 'karma', 0)}",
                'url': u.get_absolute_url()
            })

    context = {
        'suggestions': suggestions,
        'query': query
    }
    return render(request, 'search/partials/suggestions.html', context)

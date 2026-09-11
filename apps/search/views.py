from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse

from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_results(request):
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page_number = request.GET.get('page', 1)
    error = None
    results = []
    total_count = 0

    if not query or len(query) < 2:
        error = 'Введите поисковый запрос (минимум 2 символа).'
        return render(request, 'search/results.html', {
            'query': query,
            'search_type': search_type,
            'results': results,
            'total_count': total_count,
            'error': error,
        })

    if search_type == 'posts':
        queryset = Post.objects.filter(
            is_deleted=False
        ).filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        ).select_related('author', 'community').order_by('-created_at')

        total_count = queryset.count()
        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)

        if request.user.is_authenticated:
            votes_map = dict(
                PostVote.objects.filter(
                    user=request.user,
                    post__in=page_obj.object_list
                ).values_list('post_id', 'value')
            )
            for post in page_obj:
                post.user_vote = votes_map.get(post.id)

        results = page_obj

    elif search_type == 'communities':
        queryset = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).order_by('-member_count', 'name')

        total_count = queryset.count()
        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)
        results = page_obj

    elif search_type == 'users':
        queryset = User.objects.filter(
            is_active=True
        ).filter(
            Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
        ).select_related('profile').order_by('-karma', 'username')

        total_count = queryset.count()
        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)

        if request.user.is_authenticated:
            following_ids = set(
                UserFollow.objects.filter(
                    follower=request.user,
                    following__in=page_obj.object_list
                ).values_list('following_id', flat=True)
            )
            for profile_user in page_obj:
                profile_user.is_following = profile_user.id in following_ids

        results = page_obj

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
        'error': error,
    }
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        posts = Post.objects.filter(
            is_deleted=False
        ).filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        ).select_related('community').order_by('-created_at')[:3]

        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}',
            })

        communities = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).order_by('-member_count', 'name')[:3]

        for community in communities:
            suggestions.append({
                'url': reverse('communities:detail', kwargs={'slug': community.slug}),
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
            })

        users = User.objects.filter(
            is_active=True
        ).filter(
            Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
        ).order_by('-karma', 'username')[:3]

        for user in users:
            suggestions.append({
                'url': reverse('users:profile', kwargs={'username': user.username}),
                'type': 'user',
                'title': f'u/{user.username}',
                'subtitle': f'Карма: {user.karma}',
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query,
    })

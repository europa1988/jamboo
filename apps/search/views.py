from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import UserFollow
from apps.votes.models import PostVote

User = get_user_model()


def search_results(request):
    """
    Страница результатов поиска с вкладками (посты, сообщества, пользователи) и пагинацией.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'
    
    page_number = request.GET.get('page', 1)
    results = None
    total_count = 0

    if query:
        if search_type == 'posts':
            queryset = Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                is_deleted=False
            ).select_related('author', 'community').order_by('-created_at')

            paginator = Paginator(queryset, 10)
            results = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                user_votes = {
                    vote.post_id: vote.value
                    for vote in PostVote.objects.filter(
                        user=request.user,
                        post_id__in=[p.id for p in results.object_list]
                    )
                }
                for post in results.object_list:
                    post.user_vote = user_votes.get(post.id)

        elif search_type == 'communities':
            queryset = Community.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            ).order_by('-member_count')

            paginator = Paginator(queryset, 10)
            results = paginator.get_page(page_number)
            total_count = paginator.count

        elif search_type == 'users':
            queryset = User.objects.filter(
                Q(username__icontains=query) | Q(profile__bio__icontains=query)
            ).select_related('profile').order_by('username')

            paginator = Paginator(queryset, 10)
            results = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                following_ids = set(
                    UserFollow.objects.filter(
                        follower=request.user,
                        following_id__in=[u.id for u in results.object_list]
                    ).values_list('following_id', flat=True)
                )
                for profile_user in results.object_list:
                    profile_user.is_following = profile_user.id in following_ids

    return render(request, 'search/results.html', {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
    })


def search_suggestions(request):
    """
    HTMX эндпоинт автокомплита поиска.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if len(query) >= 2:
        # Поиск по постам
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community')[:5]
        
        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}'
            })

        # Поиск по сообществам
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]
        
        for community in communities:
            suggestions.append({
                'url': community.get_absolute_url(),
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников'
            })

        # Поиск по пользователям
        users = User.objects.filter(
            username__icontains=query
        )[:3]

        for profile_user in users:
            suggestions.append({
                'url': profile_user.get_absolute_url(),
                'type': 'user',
                'title': f'u/{profile_user.username}',
                'subtitle': f'Карма: {profile_user.karma}'
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query
    })

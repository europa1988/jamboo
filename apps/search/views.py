from django.shortcuts import render
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote
from apps.users.models import UserFollow

User = get_user_model()


def search_results(request):
    """
    Основная страница с результатами поиска.
    Поддерживает вкладки постов, сообществ и пользователей с пагинацией.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page_number = request.GET.get('page', 1)
    context = {
        'query': query,
        'search_type': search_type,
    }

    if not query:
        context['error'] = 'Введите поисковый запрос.'
        return render(request, 'search/results.html', context)

    if search_type == 'posts':
        queryset = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('author', 'community').order_by('-created_at')

        paginator = Paginator(queryset, 10)
        results = paginator.get_page(page_number)

        if request.user.is_authenticated and results.object_list:
            post_ids = [post.id for post in results.object_list]
            votes = PostVote.objects.filter(user=request.user, post_id__in=post_ids)
            vote_map = {v.post_id: v.value for v in votes}
            for post in results.object_list:
                post.user_vote = vote_map.get(post.id)

    elif search_type == 'communities':
        queryset = Community.objects.filter(
            name__icontains=query
        ).order_by('-member_count', 'name')

        paginator = Paginator(queryset, 10)
        results = paginator.get_page(page_number)

    elif search_type == 'users':
        queryset = User.objects.filter(
            username__icontains=query
        ).select_related('profile').order_by('username')

        paginator = Paginator(queryset, 10)
        results = paginator.get_page(page_number)

        if request.user.is_authenticated and results.object_list:
            user_ids = [u.id for u in results.object_list]
            following_ids = set(
                UserFollow.objects.filter(
                    follower=request.user,
                    following_id__in=user_ids
                ).values_list('following_id', flat=True)
            )
            for u in results.object_list:
                u.is_following = u.id in following_ids

    context['results'] = results
    context['total_count'] = paginator.count

    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX эндпоинт для автодополнения (подсказок) в поисковой строке.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community').order_by('-created_at')[:3]

        for post in posts:
            suggestions.append({
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name}',
                'url': post.get_absolute_url(),
            })

        communities = Community.objects.filter(
            name__icontains=query
        ).order_by('-member_count', 'name')[:3]

        for community in communities:
            suggestions.append({
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
                'url': community.get_absolute_url(),
            })

        users = User.objects.filter(
            username__icontains=query
        ).order_by('username')[:3]

        for user_obj in users:
            suggestions.append({
                'type': 'user',
                'title': f'u/{user_obj.username}',
                'subtitle': f'Карма: {user_obj.karma}',
                'url': user_obj.get_absolute_url(),
            })

    context = {
        'suggestions': suggestions,
        'query': query,
    }
    return render(request, 'search/partials/suggestions.html', context)

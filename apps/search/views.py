from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User
from apps.votes.models import PostVote


def search_suggestions(request):
    """HTMX эндпоинт автокомплита/подсказок поиска."""
    query = request.GET.get('q', '').strip()
    
    suggestions = []
    
    if len(query) >= 2:
        # Посты
        posts = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            is_deleted=False
        ).select_related('community', 'author')[:3]
        
        for post in posts:
            suggestions.append({
                'type': 'post',
                'title': post.title,
                'subtitle': f'c/{post.community.name} • u/{post.author.username}',
                'url': post.get_absolute_url()
            })

        # Сообщества
        communities = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )[:3]

        for community in communities:
            suggestions.append({
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников',
                'url': community.get_absolute_url()
            })

        # Пользователи
        users = User.objects.filter(
            username__icontains=query
        )[:3]
        
        for user_obj in users:
            suggestions.append({
                'type': 'user',
                'title': f'u/{user_obj.username}',
                'subtitle': f'Карма: {user_obj.karma}',
                'url': user_obj.get_absolute_url()
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query
    })


def search_results(request):
    """Основные результаты поиска с пагинацией."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    page_number = request.GET.get('page', 1)

    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    results = []
    total_count = 0
    error = None

    if query:
        if search_type == 'posts':
            qs = Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                is_deleted=False
            ).select_related('author', 'community').order_by('-created_at')

            total_count = qs.count()
            paginator = Paginator(qs, 10)
            page_obj = paginator.get_page(page_number)

            if request.user.is_authenticated and page_obj.object_list:
                posts_on_page = list(page_obj.object_list)
                votes = PostVote.objects.filter(
                    user=request.user,
                    post__in=posts_on_page
                )
                vote_map = {v.post_id: v.value for v in votes}
                for post in posts_on_page:
                    post.user_vote = vote_map.get(post.id, 0)

            results = page_obj

        elif search_type == 'communities':
            qs = Community.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            ).order_by('-member_count', 'name')

            total_count = qs.count()
            paginator = Paginator(qs, 10)
            results = paginator.get_page(page_number)

        elif search_type == 'users':
            qs = User.objects.filter(
                Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
            ).select_related('profile').order_by('username')

            total_count = qs.count()
            paginator = Paginator(qs, 10)
            page_obj = paginator.get_page(page_number)

            if request.user.is_authenticated and page_obj.object_list:
                users_on_page = list(page_obj.object_list)
                following_ids = set(request.user.following.values_list('followed_id', flat=True))
                for u in users_on_page:
                    u.is_following = u.id in following_ids

            results = page_obj

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
        'error': error
    }
    
    return render(request, 'search/results.html', context)

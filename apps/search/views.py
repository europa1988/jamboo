from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote
from apps.users.models import UserFollow

User = get_user_model()


def search_results(request):
    """Отображает полностраничные результаты поиска с пагинацией."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    context = {
        'query': query,
        'search_type': search_type,
        'results': None,
        'total_count': 0,
    }

    if not query:
        return render(request, 'search/results.html', context)

    if search_type == 'posts':
        posts_qs = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('author', 'community').order_by('-created_at')

        if request.user.is_authenticated:
            posts_qs = posts_qs.prefetch_related(
                Prefetch(
                    'votes',
                    queryset=PostVote.objects.filter(user=request.user),
                    to_attr='user_votes'
                )
            )

        paginator = Paginator(posts_qs, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        if request.user.is_authenticated:
            for post in page_obj:
                if hasattr(post, 'user_votes'):
                    post.user_vote = post.user_votes[0].value if post.user_votes else None
                else:
                    post.user_vote = post.get_user_vote(request.user)

        context['results'] = page_obj
        context['total_count'] = paginator.count

    elif search_type == 'communities':
        communities_qs = Community.objects.filter(
            name__icontains=query
        ).order_by('-member_count', 'name')

        paginator = Paginator(communities_qs, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['results'] = page_obj
        context['total_count'] = paginator.count

    elif search_type == 'users':
        users_qs = User.objects.filter(
            username__icontains=query
        ).select_related('profile').prefetch_related('posts', 'comments').order_by('username')

        paginator = Paginator(users_qs, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        if request.user.is_authenticated:
            # Предотвращаем N+1 для подписок
            following_user_ids = set(
                UserFollow.objects.filter(follower=request.user).values_list('following_id', flat=True)
            )
            for profile_user in page_obj:
                profile_user.is_following = profile_user.id in following_user_ids

        context['results'] = page_obj
        context['total_count'] = paginator.count

    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """HTMX эндпоинт автокомплита поиска."""
    query = request.GET.get('q', '').strip()
    
    suggestions = []
    
    if len(query) >= 2:
        # Поиск по постам
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community', 'author')[:5]
        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f"Пост в c/{post.community.name} • u/{post.author.username}"
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
        ).order_by('username')[:3]
        for user in users:
            suggestions.append({
                'url': reverse('users:profile', kwargs={'username': user.username}),
                'type': 'user',
                'title': f"u/{user.username}",
                'subtitle': f"Карма: {user.karma}"
            })

    context = {
        'suggestions': suggestions,
        'query': query,
    }
    
    html = render_to_string('search/partials/suggestions.html', context, request=request)
    return HttpResponse(html)

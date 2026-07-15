from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from apps.posts.models import Post
from apps.communities.models import Community
from apps.votes.models import PostVote

User = get_user_model()


def search_suggestions(request):
    """HTMX эндпоинт автокомплита поиска."""
    query = request.GET.get('q', '').strip()
    
    suggestions = []
    
    if len(query) >= 2:
        # Поиск по сообществам
        communities = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )[:3]
        for c in communities:
            suggestions.append({
                'type': 'community',
                'title': f'c/{c.name}',
                'subtitle': f'{c.member_count} участников',
                'url': reverse('communities:detail', kwargs={'slug': c.slug})
            })

        # Поиск по постам
        posts = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            is_deleted=False
        ).select_related('community')[:5]
        for p in posts:
            suggestions.append({
                'type': 'post',
                'title': p.title,
                'subtitle': f'в c/{p.community.name}',
                'url': p.get_absolute_url()
            })

        # Поиск по пользователям
        users = User.objects.filter(
            username__icontains=query
        )[:3]
        for u in users:
            suggestions.append({
                'type': 'user',
                'title': f'u/{u.username}',
                'subtitle': f'Карма: {u.karma}',
                'url': reverse('users:profile', kwargs={'username': u.username})
            })

    context = {
        'suggestions': suggestions,
        'query': query
    }

    html = render_to_string('search/partials/suggestions.html', context, request=request)
    return HttpResponse(html)


def search_results(request):
    """Страница с результатами поиска."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    page_number = request.GET.get('page', 1)

    results = []
    total_count = 0

    if query:
        if search_type == 'posts':
            queryset = Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                is_deleted=False
            ).select_related('author', 'community')

            if request.user.is_authenticated:
                queryset = queryset.prefetch_related(
                    Prefetch('votes', queryset=PostVote.objects.filter(user=request.user), to_attr='current_user_vote')
                )

            paginator = Paginator(queryset, 10)
            results = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                for post in results:
                    post.user_vote = post.current_user_vote[0].value if post.current_user_vote else None

        elif search_type == 'communities':
            queryset = Community.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            ).order_by('-member_count')

            paginator = Paginator(queryset, 12)
            results = paginator.get_page(page_number)
            total_count = paginator.count

        elif search_type == 'users':
            queryset = User.objects.filter(
                Q(username__icontains=query) | Q(profile__bio__icontains=query)
            ).select_related('profile').order_by('-karma')

            paginator = Paginator(queryset, 15)
            results = paginator.get_page(page_number)
            total_count = paginator.count

            if request.user.is_authenticated:
                from apps.users.models import UserFollow
                following_ids = UserFollow.objects.filter(follower=request.user).values_list('following_id', flat=True)
                for profile_user in results:
                    profile_user.is_following = profile_user.id in following_ids

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
    }
    
    return render(request, 'search/results.html', context)

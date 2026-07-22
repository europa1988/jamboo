from django.shortcuts import render
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator
from django.urls import reverse
from django.http import HttpResponse
from django.template.loader import render_to_string
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_results(request):
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts').strip()
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page_number = request.GET.get('page', 1)

    context = {
        'query': query,
        'search_type': search_type,
        'results': None,
        'total_count': 0,
        'error': None,
    }
    
    if 'q' in request.GET:
        if len(query) < 2:
            context['error'] = "Длина запроса должна быть не менее 2 символов."
            return render(request, 'search/results.html', context)

        if search_type == 'posts':
            # Perform post search
            if request.user.is_authenticated:
                queryset = Post.objects.filter(is_deleted=False).filter(
                    Q(title__icontains=query) | Q(content__icontains=query)
                ).select_related('author', 'community').prefetch_related(
                    Prefetch('votes', queryset=PostVote.objects.filter(user=request.user), to_attr='user_votes')
                ).order_by('-created_at')
            else:
                queryset = Post.objects.filter(is_deleted=False).filter(
                    Q(title__icontains=query) | Q(content__icontains=query)
                ).select_related('author', 'community').order_by('-created_at')

        elif search_type == 'communities':
            # Perform community search
            queryset = Community.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            ).order_by('-member_count')

        elif search_type == 'users':
            # Perform user search
            queryset = User.objects.filter(
                username__icontains=query
            ).order_by('username')

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)

        # Post-process for extra attributes
        if search_type == 'posts':
            if request.user.is_authenticated:
                for post in page_obj:
                    post.user_vote = post.user_votes[0].value if post.user_votes else None
            else:
                for post in page_obj:
                    post.user_vote = None
        elif search_type == 'users':
            if request.user.is_authenticated:
                following_ids = set(UserFollow.objects.filter(follower=request.user).values_list('following_id', flat=True))
                for u in page_obj:
                    u.is_following = u.id in following_ids
            else:
                for u in page_obj:
                    u.is_following = False

        context['results'] = page_obj
        context['total_count'] = paginator.count

    return render(request, 'search/results.html', context)


def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if len(query) >= 2:
        # 1. Посты (до 5 штук)
        posts = Post.objects.filter(
            is_deleted=False
        ).filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        ).select_related('community')[:5]
        
        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f"c/{post.community.name} • {post.score} ⬆"
            })

        # 2. Сообщества (до 3 штук)
        communities = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )[:3]
        
        for community in communities:
            suggestions.append({
                'url': reverse('communities:detail', kwargs={'slug': community.slug}),
                'type': 'community',
                'title': f"c/{community.name}",
                'subtitle': f"{community.member_count} участников"
            })

        # 3. Пользователи (до 3 штук)
        users = User.objects.filter(
            username__icontains=query
        )[:3]

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

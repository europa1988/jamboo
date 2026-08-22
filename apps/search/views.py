from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.shortcuts import render
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User
from apps.votes.models import PostVote


def search_results(request):
    """
    Основная страница результатов поиска с пагинацией и оптимизацией Prefetch.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    page_number = request.GET.get('page', 1)
    context = {
        'query': query,
        'search_type': search_type,
        'total_count': 0,
        'page_obj': None,
        'error': None,
    }

    if not query:
        return render(request, 'search/results.html', context)

    if search_type == 'posts':
        queryset = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('author', 'community')

        if request.user.is_authenticated:
            queryset = queryset.prefetch_related(
                Prefetch(
                    'votes',
                    queryset=PostVote.objects.filter(user=request.user),
                    to_attr='user_votes'
                )
            )

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)

        if request.user.is_authenticated:
            for post in page_obj.object_list:
                votes = getattr(post, 'user_votes', [])
                post.user_vote = votes[0].value if votes else 0

        context['page_obj'] = page_obj
        context['total_count'] = paginator.count

    elif search_type == 'communities':
        queryset = Community.objects.filter(
            name__icontains=query,
            is_active=True
        ).order_by('-member_count')

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)

        context['page_obj'] = page_obj
        context['total_count'] = paginator.count

    elif search_type == 'users':
        queryset = User.objects.filter(
            username__icontains=query,
            is_active=True
        ).order_by('-karma')

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)

        context['page_obj'] = page_obj
        context['total_count'] = paginator.count

    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    HTMX подсказки для выпадающего списка автодополнения.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('author', 'community')[:3]
        for post in posts:
            suggestions.append({
                'title': post.title,
                'subtitle': f'в r/{post.community.name}' if post.community else 'от ' + post.author.username,
                'url': post.get_absolute_url(),
                'type': 'post',
            })

        communities = Community.objects.filter(
            name__icontains=query,
            is_active=True
        )[:3]
        for community in communities:
            suggestions.append({
                'title': community.name,
                'subtitle': f'{community.member_count} участников',
                'url': community.get_absolute_url(),
                'type': 'community',
            })

        users = User.objects.filter(
            username__icontains=query,
            is_active=True
        )[:3]
        for user in users:
            suggestions.append({
                'title': user.username,
                'subtitle': f'{user.karma} кармы',
                'url': user.get_absolute_url(),
                'type': 'user',
            })

    context = {
        'query': query,
        'suggestions': suggestions,
    }
    return render(request, 'search/partials/suggestions.html', context)
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import render
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from apps.posts.models import Post
from apps.communities.models import Community

User = get_user_model()


def search_results(request):
    """Основная страница поиска."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    page_number = request.GET.get('page', 1)
    
    results = []
    total_count = 0

    if query:
        if search_type == 'posts':
            posts_qs = Post.objects.filter(
                title__icontains=query,
                is_deleted=False
            ).select_related('community', 'author')

            # Предзагрузка голосов
            if request.user.is_authenticated:
                from django.db.models import Prefetch
                from apps.votes.models import PostVote
                posts_qs = posts_qs.prefetch_related(
                    Prefetch(
                        'votes',
                        queryset=PostVote.objects.filter(user=request.user),
                        to_attr='user_vote_obj'
                    )
                )

            total_count = posts_qs.count()
            paginator = Paginator(posts_qs, 10)
            results = paginator.get_page(page_number)

            # Обработка user_vote для шаблона
            if request.user.is_authenticated:
                for post in results:
                    post.user_vote = post.user_vote_obj[0].value if post.user_vote_obj else None

        elif search_type == 'communities':
            communities_qs = Community.objects.filter(name__icontains=query)
            total_count = communities_qs.count()
            paginator = Paginator(communities_qs, 12)
            results = paginator.get_page(page_number)

        elif search_type == 'users':
            users_qs = User.objects.filter(username__icontains=query).select_related('profile').order_by('username')
            total_count = users_qs.count()
            paginator = Paginator(users_qs, 15)
            results = paginator.get_page(page_number)

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_count': total_count,
    }
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
        ).select_related('community')[:5]
        
        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f'в c/{post.community.name}'
            })

        # Поиск по сообществам
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]
        
        for community in communities:
            suggestions.append({
                'url': f'/c/{community.slug}/',
                'type': 'community',
                'title': f'c/{community.name}',
                'subtitle': f'{community.member_count} участников'
            })

    context = {
        'suggestions': suggestions,
        'query': query
    }
    
    html = render_to_string('search/partials/suggestions.html', context, request=request)
    return HttpResponse(html)
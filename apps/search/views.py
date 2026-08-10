from django.shortcuts import render
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator
from django.urls import reverse
from apps.posts.models import Post
from apps.communities.models import Community
from apps.users.models import User, UserFollow
from apps.votes.models import PostVote


def search_results(request):
    """
    Полностраничный поиск постов, сообществ или пользователей с пагинацией по 10 элементов.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')
    if search_type not in ['posts', 'communities', 'users']:
        search_type = 'posts'

    error = None
    if not query:
        error = "Введите поисковый запрос"
    elif len(query) < 2:
        error = "Поисковый запрос должен содержать не менее 2 символов"

    if error:
        return render(request, 'search/results.html', {
            'query': query,
            'search_type': search_type,
            'error': error,
        })

    # Выбор базового QuerySet в зависимости от типа поиска
    if search_type == 'posts':
        if request.user.is_authenticated:
            queryset = Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                is_deleted=False
            ).select_related('author', 'community').prefetch_related(
                Prefetch('votes', queryset=PostVote.objects.filter(user=request.user), to_attr='user_votes')
            ).order_by('-created_at')
        else:
            queryset = Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                is_deleted=False
            ).select_related('author', 'community').order_by('-created_at')

    elif search_type == 'communities':
        queryset = Community.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        ).order_by('-member_count')

    elif search_type == 'users':
        queryset = User.objects.filter(
            username__icontains=query,
            is_active=True
        ).select_related('profile').order_by('username')

    # Пагинация — по 10 результатов на страницу
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    results = page_obj.object_list

    # Вычисление пользовательских полей после пагинации, чтобы избежать потери атрибутов
    if search_type == 'posts':
        if request.user.is_authenticated:
            for post in results:
                votes_list = getattr(post, 'user_votes', [])
                post.user_vote = votes_list[0].value if votes_list else None
        else:
            for post in results:
                post.user_vote = None

    elif search_type == 'users':
        if request.user.is_authenticated:
            following_ids = set(
                UserFollow.objects.filter(follower=request.user, following__in=results)
                .values_list('following_id', flat=True)
            )
            for profile_user in results:
                profile_user.is_following = profile_user.id in following_ids
        else:
            for profile_user in results:
                profile_user.is_following = False

    return render(request, 'search/results.html', {
        'query': query,
        'search_type': search_type,
        'results': page_obj,
        'total_count': paginator.count,
    })


def search_suggestions(request):
    """
    HTMX эндпоинт автодополнения (поисковых подсказок).
    Ожидает в контексте список 'suggestions' с элементами, содержащими:
    'url', 'type', 'title', и 'subtitle'.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []

    if len(query) >= 2:
        # Поиск по постам (до 5 штук)
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community', 'author')[:5]

        for post in posts:
            suggestions.append({
                'url': post.get_absolute_url(),
                'type': 'post',
                'title': post.title,
                'subtitle': f"в c/{post.community.name} • u/{post.author.username}",
            })

        # Поиск по сообществам (до 3 штук)
        communities = Community.objects.filter(
            name__icontains=query,
            is_active=True
        )[:3]

        for community in communities:
            suggestions.append({
                'url': reverse('communities:detail', kwargs={'slug': community.slug}),
                'type': 'community',
                'title': f"c/{community.name}",
                'subtitle': f"{community.member_count} участников",
            })

        # Поиск по пользователям (до 3 штук)
        users = User.objects.filter(
            username__icontains=query,
            is_active=True
        ).order_by('username')[:3]

        for user in users:
            suggestions.append({
                'url': reverse('users:profile', kwargs={'username': user.username}),
                'type': 'user',
                'title': f"u/{user.username}",
                'subtitle': f"Карма: {user.karma}",
            })

    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query,
    })

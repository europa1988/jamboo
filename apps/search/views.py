from django.shortcuts import render
from django.db.models import Q
from django.core.paginator import Paginator

from apps.posts.models import Post
from apps.communities.models import Community


def search_results(request):
    """
    Поиск по постам, сообществам и пользователям.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'posts')  # posts, communities, users
    
    context = {
        'query': query,
        'search_type': search_type,
    }
    
    if not query or len(query) < 2:
        context['error'] = 'Введите минимум 2 символа для поиска'
        return render(request, 'search/results.html', context)
    
    if search_type == 'posts':
        # Поиск по постам
        posts = Post.objects.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query),
            is_deleted=False
        ).select_related('author', 'community').prefetch_related('votes').order_by('-score', '-created_at')
        
        # Добавляем user_vote
        if request.user.is_authenticated:
            for post in posts:
                post.user_vote = post.get_user_vote(request.user)
        
        paginator = Paginator(posts, 20)
        page_number = request.GET.get('page', 1)
        context['results'] = paginator.get_page(page_number)
        context['total_count'] = posts.count()
        
    elif search_type == 'communities':
        # Поиск по сообществам
        communities = Community.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        ).order_by('-member_count')
        
        # Проверяем членство
        if request.user.is_authenticated:
            for community in communities:
                community.is_member = community.members.filter(
                    user=request.user
                ).exists()
        
        paginator = Paginator(communities, 20)
        page_number = request.GET.get('page', 1)
        context['results'] = paginator.get_page(page_number)
        context['total_count'] = communities.count()
        
    elif search_type == 'users':
        # Поиск по пользователям
        from apps.users.models import User
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(profile__bio__icontains=query)
        ).select_related('profile').order_by('-karma')
        
        paginator = Paginator(users, 20)
        page_number = request.GET.get('page', 1)
        context['results'] = paginator.get_page(page_number)
        context['total_count'] = users.count()
    
    return render(request, 'search/results.html', context)


def search_suggestions(request):
    """
    Автодополнение поиска (HTMX).
    Возвращает подсказки при вводе.
    """
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return render(request, 'search/partials/suggestions.html', {
            'suggestions': []
        })
    
    # Ищем посты, сообщества и пользователей
    posts = Post.objects.filter(
        title__icontains=query,
        is_deleted=False
    ).select_related('community')[:3]
    
    communities = Community.objects.filter(
        name__icontains=query
    )[:3]
    
    from apps.users.models import User
    users = User.objects.filter(
        username__icontains=query
    )[:3]
    
    suggestions = []
    
    for post in posts:
        suggestions.append({
            'type': 'post',
            'title': post.title,
            'url': post.get_absolute_url(),
            'subtitle': f'c/{post.community.name}'
        })
    
    for community in communities:
        suggestions.append({
            'type': 'community',
            'title': f'c/{community.name}',
            'url': f'/c/{community.slug}/',
            'subtitle': f'{community.member_count} участников'
        })
    
    for user in users:
        suggestions.append({
            'type': 'user',
            'title': f'u/{user.username}',
            'url': f'/u/{user.username}/',
            'subtitle': f'Карма: {user.karma}'
        })
    
    return render(request, 'search/partials/suggestions.html', {
        'suggestions': suggestions,
        'query': query
    })
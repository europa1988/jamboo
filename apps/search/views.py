from django.http import HttpResponse
from django.template.loader import render_to_string
from apps.posts.models import Post
from apps.communities.models import Community


def autocomplete(request):
    """HTMX эндпоинт автокомплита поиска."""
    query = request.GET.get('q', '').strip()
    
    results = []
    
    if len(query) >= 2:
        # Поиск по постам
        posts = Post.objects.filter(
            title__icontains=query,
            is_deleted=False
        ).select_related('community')[:5]
        
        # Поиск по сообществам
        communities = Community.objects.filter(
            name__icontains=query
        )[:3]
        
        results = {
            'posts': posts,
            'communities': communities,
            'query': query
        }
    
    html = render_to_string('search/partials/autocomplete_results.html', results, request=request)
    return HttpResponse(html)
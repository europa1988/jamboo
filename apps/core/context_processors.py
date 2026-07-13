from apps.communities.models import Community


def global_context(request):
    """
    Глобальный контекст для всех шаблонов.
    Добавляет популярные сообщества и счётчик уведомлений.
    """
    context = {
        'popular_communities': Community.objects.filter(
            is_active=True
        ).order_by('-member_count')[:10],
        'trending_communities': Community.objects.filter(
            is_active=True
        ).order_by('-created_at')[:5],
    }
    
    # Счётчик непрочитанных уведомлений
    if request.user.is_authenticated:
        context['unread_notifications_count'] = request.user.notifications.filter(
            is_read=False
        ).count()
    else:
        context['unread_notifications_count'] = 0
    
    return context
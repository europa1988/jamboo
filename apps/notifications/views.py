from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_list(request):
    """
    Страница со всеми уведомлениями пользователя.
    """
    notifications = request.user.notifications.all().select_related('sender')
    
    # Помечаем все как прочитанные при просмотре страницы
    unread = notifications.filter(is_read=False)
    unread_count = unread.count()
    
    context = {
        'notifications': notifications[:50],
        'unread_count': unread_count,
    }
    
    return render(request, 'notifications/list.html', context)


@login_required
def notification_badge(request):
    """
    Возвращает HTML бейджа с количеством непрочитанных (HTMX polling).
    """
    count = request.user.notifications.filter(is_read=False).count()
    return render(request, 'notifications/partials/badge.html', {
        'unread_count': count
    })


@login_required
@require_POST
def notification_mark_read(request, notification_id):
    """
    Помечает одно уведомление как прочитанное (HTMX).
    """
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )
    
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    
    # Возвращаем обновлённый элемент
    return render(request, 'notifications/partials/notification_item.html', {
        'notification': notification
    })


@login_required
@require_POST
def notification_mark_all_read(request):
    """
    Помечает все уведомления как прочитанные (HTMX).
    """
    request.user.notifications.filter(is_read=False).update(is_read=True)
    
    # Возвращаем пустой бейдж
    return render(request, 'notifications/partials/badge.html', {
        'unread_count': 0
    })


@login_required
@require_POST
def notification_delete(request, notification_id):
    """
    Удаляет уведомление (HTMX).
    """
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )
    
    notification.delete()
    
    return HttpResponse('')
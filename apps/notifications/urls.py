from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Список уведомлений
    path('notifications/', views.notification_list, name='list'),
    # Бейдж с количеством (HTMX polling)
    path('notifications/badge/', views.notification_badge, name='badge'),
    # Пометить как прочитанное
    path('notifications/<int:notification_id>/read/', views.notification_mark_read, name='mark_read'),
    # Пометить все как прочитанные
    path('notifications/read-all/', views.notification_mark_all_read, name='mark_all_read'),
    # Удалить уведомление
    path('notifications/<int:notification_id>/delete/', views.notification_delete, name='delete'),
]
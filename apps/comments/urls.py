from django.urls import path
from . import views

app_name = 'comments'

urlpatterns = [
    # Создание комментария к посту
    path('post/<int:post_id>/create/', views.comment_create, name='create'),
    # Получение формы ответа (HTMX)
    path('<int:comment_id>/reply-form/', views.comment_reply_form, name='reply_form'),
    # Редактирование
    path('<int:comment_id>/edit/', views.comment_edit, name='edit'),
    # Удаление
    path('<int:comment_id>/delete/', views.comment_delete, name='delete'),
]
from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    # Главная страница
    path('', views.HomeView.as_view(), name='home'),
    # Создание поста
    path('create/', views.PostCreateView.as_view(), name='create'),
    # Детальная страница поста
    path('c/<slug:community_slug>/post/<int:post_id>/<slug:post_slug>/', 
         views.PostDetailView.as_view(), name='detail'),
    # Удаление поста
    path('post/<int:post_id>/delete/', views.post_delete_view, name='delete'),
]
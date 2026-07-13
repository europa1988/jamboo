from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Регистрация
    path('register/', views.register_view, name='register'),
    # Вход
    path('login/', views.login_view, name='login'),
    # Выход
    path('logout/', views.logout_view, name='logout'),
    # Профиль пользователя
    path('u/<str:username>/', views.ProfileView.as_view(), name='profile'),
    # Посты пользователя (HTMX)
    path('u/<str:username>/posts/', views.user_posts, name='user_posts'),
    # Комментарии пользователя (HTMX)
    path('u/<str:username>/comments/', views.user_comments, name='user_comments'),
    # Редактирование профиля
    path('settings/', views.ProfileEditView.as_view(), name='profile_edit'),
    # Подписка/отписка (HTMX)
    path('u/<str:username>/follow/', views.follow_user, name='follow'),
]
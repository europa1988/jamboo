from django.urls import path
from . import views

app_name = 'communities'

urlpatterns = [
    # Список сообществ
    path('communities/', views.CommunityListView.as_view(), name='list'),
    # Детальная страница
    path('c/<slug:slug>/', views.CommunityDetailView.as_view(), name='detail'),
    # Создание
    path('communities/create/', views.CommunityCreateView.as_view(), name='create'),
    # Присоединение (HTMX)
    path('c/<slug:slug>/join/', views.community_join, name='join'),
    # Выход (HTMX)
    path('c/<slug:slug>/leave/', views.community_leave, name='leave'),
    # Участники
    path('c/<slug:slug>/members/', views.community_members, name='members'),
]
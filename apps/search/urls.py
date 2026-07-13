from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    # Результаты поиска
    path('search/', views.search_results, name='results'),
    # Автодополнение (HTMX)
    path('search/suggestions/', views.search_suggestions, name='suggestions'),
]
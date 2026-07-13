from django.urls import path
from . import views

app_name = 'votes'

urlpatterns = [
    # Голосование за пост
    path('post/<int:post_id>/', views.vote_post, name='post'),
    # Голосование за комментарий
    path('comment/<int:comment_id>/', views.vote_comment, name='comment'),
]

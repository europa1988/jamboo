from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.posts.urls', namespace='posts')),
    path('', include('apps.users.urls', namespace='users')),
    path('', include('apps.communities.urls', namespace='communities')),
    path('', include('apps.search.urls', namespace='search')),
    path('', include('apps.notifications.urls', namespace='notifications')),  # ДОБАВИЛИ
    path('comments/', include('apps.comments.urls', namespace='comments')),
    path('vote/', include('apps.votes.urls', namespace='votes')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
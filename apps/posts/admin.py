from django.contrib import admin
from .models import Post, PostSave, PostReport


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'community', 'score', 'created_at', 'is_deleted']
    list_filter = ['post_type', 'is_nsfw', 'is_deleted', 'created_at']
    search_fields = ['title', 'content']
    date_hierarchy = 'created_at'


@admin.register(PostReport)
class PostReportAdmin(admin.ModelAdmin):
    list_display = ['post', 'reporter', 'reason', 'is_resolved', 'created_at']
    list_filter = ['reason', 'is_resolved', 'created_at']
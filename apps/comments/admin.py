from django.contrib import admin
from .models import Comment, CommentReport


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'post', 'score', 'depth', 'created_at']
    list_filter = ['depth', 'is_deleted', 'created_at']


@admin.register(CommentReport)
class CommentReportAdmin(admin.ModelAdmin):
    list_display = ['comment', 'reporter', 'reason', 'is_resolved']
    list_filter = ['reason', 'is_resolved']
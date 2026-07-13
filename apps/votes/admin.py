from django.contrib import admin
from .models import PostVote, CommentVote


@admin.register(PostVote)
class PostVoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'value', 'created_at']
    list_filter = ['value', 'created_at']


@admin.register(CommentVote)
class CommentVoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'comment', 'value', 'created_at']
    list_filter = ['value', 'created_at']
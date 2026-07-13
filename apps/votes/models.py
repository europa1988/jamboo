from django.db import models
from django.conf import settings


class PostVote(models.Model):
    """
    Голос за пост (+1 или -1).
    """
    UPVOTE = 1
    DOWNVOTE = -1
    
    VALUE_CHOICES = [
        (UPVOTE, 'Апвоут'),
        (DOWNVOTE, 'Даунвоут'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='post_votes'
    )
    post = models.ForeignKey(
        'posts.Post',
        on_delete=models.CASCADE,
        related_name='votes'
    )
    value = models.SmallIntegerField(choices=VALUE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']  # Один пользователь — один голос
        verbose_name = 'Голос за пост'
        verbose_name_plural = 'Голоса за посты'


class CommentVote(models.Model):
    """
    Голос за комментарий.
    """
    UPVOTE = 1
    DOWNVOTE = -1
    
    VALUE_CHOICES = [
        (UPVOTE, 'Апвоут'),
        (DOWNVOTE, 'Даунвоут'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comment_votes'
    )
    comment = models.ForeignKey(
        'comments.Comment',
        on_delete=models.CASCADE,
        related_name='votes'
    )
    value = models.SmallIntegerField(choices=VALUE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'comment']
        verbose_name = 'Голос за комментарий'
        verbose_name_plural = 'Голоса за комментарии'
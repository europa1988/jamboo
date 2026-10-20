from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Notification(models.Model):
    """
    Уведомление пользователя.
    """
    TYPE_CHOICES = [
        ('comment_post', 'Новый комментарий к посту'),
        ('reply', 'Ответ на комментарий'),
        ('mention', 'Упоминание'),
        ('upvote_post', 'Апвоут поста'),
        ('upvote_comment', 'Апвоут комментария'),
        ('follow', 'Новый подписчик'),
        ('mod_action', 'Модераторское действие'),
        ('community_invite', 'Приглашение в сообщество'),
    ]
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications_sent',
        null=True,
        blank=True
    )
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    
    # Generic FK: может указывать на Post, Comment и т.д.
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    message = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.notification_type} для {self.recipient}'
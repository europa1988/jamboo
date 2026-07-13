from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class ModLog(models.Model):
    """
    Лог действий модераторов.
    """
    ACTION_CHOICES = [
        ('remove_post', 'Удаление поста'),
        ('remove_comment', 'Удаление комментария'),
        ('ban_user', 'Бан пользователя'),
        ('unban_user', 'Разбан'),
        ('pin_post', 'Закрепление поста'),
        ('unpin_post', 'Открепление поста'),
        ('edit_community', 'Изменение сообщества'),
    ]
    
    community = models.ForeignKey(
        'communities.Community',
        on_delete=models.CASCADE,
        related_name='mod_logs'
    )
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mod_actions'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Лог модерации'
        verbose_name_plural = 'Логи модерации'
        ordering = ['-created_at']


class Report(models.Model):
    """
    Универсальная жалоба (на пост или комментарий).
    Используем GenericForeignKey для связи с любой моделью.
    """
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('resolved', 'Решена'),
        ('dismissed', 'Отклонена'),
    ]
    
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_made'
    )
    reason = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    
    # Generic FK: может указывать на Post или Comment
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_resolved'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Жалоба'
        verbose_name_plural = 'Жалобы'


class RemovalReason(models.Model):
    """
    Причина удаления контента.
    """
    community = models.ForeignKey(
        'communities.Community',
        on_delete=models.CASCADE,
        related_name='removal_reasons'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    class Meta:
        verbose_name = 'Причина удаления'
        verbose_name_plural = 'Причины удаления'
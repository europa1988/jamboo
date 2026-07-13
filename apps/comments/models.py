from django.db import models
from django.conf import settings


class Comment(models.Model):
    """
    Комментарий к посту (древовидная структура).
    """
    post = models.ForeignKey(
        'posts.Post',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    # Self-referential: комментарий может быть ответом на другой комментарий
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.TextField(verbose_name='Текст')
    score = models.IntegerField(default=0, verbose_name='Рейтинг')
    
    # Для оптимизации: глубина вложенности
    depth = models.PositiveSmallIntegerField(default=0)
    
    # Флаги
    is_deleted = models.BooleanField(default=False, verbose_name='Удалён')
    
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    def get_user_vote(self, user):
        """
        Возвращает голос текущего пользователя за этот комментарий.
        """
        if not user or not user.is_authenticated:
            return None
        vote = self.votes.filter(user=user).first()
        return vote.value if vote else None
    
    def update_score(self):
        """
        Пересчитывает рейтинг комментария.
        """
        from django.db.models import Sum
        result = self.votes.aggregate(total=Sum('value'))
        self.score = result['total'] or 0
        self.save(update_fields=['score'])

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['created_at']
    
    def __str__(self):
        return f'Комментарий {self.author} к {self.post}'
    
    def save(self, *args, **kwargs):
        """
        Переопределяем save для автоматического расчёта глубины.
        """
        if self.parent:
            self.depth = self.parent.depth + 1
        super().save(*args, **kwargs)


class CommentSave(models.Model):
    """
    Сохранённые комментарии.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_comments'
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='saves'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'comment']


class CommentReport(models.Model):
    """
    Жалоба на комментарий.
    """
    REASON_CHOICES = [
        ('spam', 'Спам'),
        ('harassment', 'Домогательство'),
        ('hate', 'Разжигание ненависти'),
        ('other', 'Другое'),
    ]
    
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comment_reports'
    )
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
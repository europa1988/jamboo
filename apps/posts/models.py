from django.db import models
from django.conf import settings
from django.urls import reverse


class Post(models.Model):
    """
    Пост в сообществе.
    """
    # Типы постов
    TEXT = 'text'
    LINK = 'link'
    IMAGE = 'image'
    VIDEO = 'video'
    POLL = 'poll'
    
    TYPE_CHOICES = [
        (TEXT, 'Текст'),
        (LINK, 'Ссылка'),
        (IMAGE, 'Изображение'),
        (VIDEO, 'Видео'),
        (POLL, 'Опрос'),
    ]
    
    title = models.CharField(max_length=300, verbose_name='Заголовок')
    slug = models.SlugField(max_length=300, verbose_name='URL')
    content = models.TextField(blank=True, verbose_name='Текст')
    url = models.URLField(blank=True, verbose_name='Внешняя ссылка')
    post_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default=TEXT,
        verbose_name='Тип'
    )
    image = models.ImageField(
        upload_to='post_images/',
        blank=True,
        null=True,
        verbose_name='Изображение'
    )
    
    # Связи
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    community = models.ForeignKey(
        'communities.Community',
        on_delete=models.CASCADE,
        related_name='posts'
    )
    
    # Статистика
    score = models.IntegerField(default=0, verbose_name='Рейтинг')
    comment_count = models.PositiveIntegerField(default=0, verbose_name='Комментариев')
    
    # Флаги
    is_pinned = models.BooleanField(default=False, verbose_name='Закреплён')
    is_nsfw = models.BooleanField(default=False, verbose_name='NSFW')
    is_spoiler = models.BooleanField(default=False, verbose_name='Спойлер')
    is_deleted = models.BooleanField(default=False, verbose_name='Удалён')
    
    # Даты
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    edited_at = models.DateTimeField(null=True, blank=True, verbose_name='Изменён')
    
    def get_user_vote(self, user):
        """
        Возвращает голос текущего пользователя за этот пост.
        +1 = апвоут, -1 = даунвоут, None = не голосовал.
        """
        if not user or not user.is_authenticated:
            return None
        vote = self.votes.filter(user=user).first()
        return vote.value if vote else None
    
    def update_score(self):
        """
        Пересчитывает рейтинг поста на основе всех голосов.
        """
        from django.db.models import Sum
        result = self.votes.aggregate(total=Sum('value'))
        self.score = result['total'] or 0
        self.save(update_fields=['score'])

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['community', '-created_at']),
            models.Index(fields=['author', '-created_at']),
        ]
    
    def __str__(self):
        return self.title[:50]

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title) or 'post'
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """
        Возвращает URL поста. Используется в шаблонах.
        """
        community_slug = self.community.slug if self.community and self.community.slug else 'general'
        post_slug = self.slug if self.slug else 'post'
        return reverse('posts:detail', kwargs={
            'community_slug': community_slug,
            'post_id': self.id,
            'post_slug': post_slug
        })


class PostSave(models.Model):
    """
    Сохранённые посты пользователя.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_posts'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='saves'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']
        verbose_name = 'Сохранённый пост'
        verbose_name_plural = 'Сохранённые посты'


class PostReport(models.Model):
    """
    Жалоба на пост.
    """
    REASON_CHOICES = [
        ('spam', 'Спам'),
        ('harassment', 'Домогательство'),
        ('hate', 'Разжигание ненависти'),
        ('nsfw', 'NSFW без метки'),
        ('misinformation', 'Дезинформация'),
        ('other', 'Другое'),
    ]
    
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='post_reports'
    )
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Жалоба на пост'
        verbose_name_plural = 'Жалобы на посты'
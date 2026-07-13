from django.db import models
from django.conf import settings


class Community(models.Model):
    """
    Сообщество (аналог сабреддита).
    """
    # Типы сообществ
    PUBLIC = 'public'
    RESTRICTED = 'restricted'
    PRIVATE = 'private'
    
    TYPE_CHOICES = [
        (PUBLIC, 'Открытое'),
        (RESTRICTED, 'Ограниченное'),
        (PRIVATE, 'Закрытое'),
    ]
    
    name = models.CharField(max_length=50, unique=True, verbose_name='Название')
    slug = models.SlugField(max_length=50, unique=True, verbose_name='URL-имя')
    description = models.TextField(max_length=1000, verbose_name='Описание')
    community_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=PUBLIC,
        verbose_name='Тип'
    )
    avatar = models.ImageField(
        upload_to='community_avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар'
    )
    banner = models.ImageField(
        upload_to='community_banners/',
        blank=True,
        null=True,
        verbose_name='Баннер'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    # Создатель сообщества
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_communities'
    )
    # Количество участников (кэшируем для быстроты)
    member_count = models.PositiveIntegerField(default=0, verbose_name='Участников')
    
    class Meta:
        verbose_name = 'Сообщество'
        verbose_name_plural = 'Сообщества'
        ordering = ['-member_count']  # Сортировка по популярности
    
    def __str__(self):
        return f'c/{self.name}'


class CommunityMember(models.Model):
    """
    Участник сообщества с ролью.
    """
    MEMBER = 'member'
    MODERATOR = 'moderator'
    ADMIN = 'admin'
    
    ROLE_CHOICES = [
        (MEMBER, 'Участник'),
        (MODERATOR, 'Модератор'),
        (ADMIN, 'Администратор'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_memberships'
    )
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name='members'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=MEMBER
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'community']
        verbose_name = 'Участник сообщества'
        verbose_name_plural = 'Участники сообществ'


class CommunityRule(models.Model):
    """
    Правила сообщества.
    """
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name='rules'
    )
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    description = models.TextField(blank=True, verbose_name='Описание')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')
    
    class Meta:
        ordering = ['order']
        verbose_name = 'Правило'
        verbose_name_plural = 'Правила'


class CommunityBan(models.Model):
    """
    Бан пользователя в сообществе.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_bans'
    )
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name='bans'
    )
    reason = models.TextField(blank=True, verbose_name='Причина')
    banned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='issued_bans'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='Истекает')
    
    class Meta:
        unique_together = ['user', 'community']
        verbose_name = 'Бан в сообществе'
        verbose_name_plural = 'Баны в сообществах'
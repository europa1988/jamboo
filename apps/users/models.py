from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    """
    Расширенная модель пользователя.
    AbstractUser уже содержит: username, password, email, first_name, last_name, is_active, is_staff, date_joined
    """
    # Дополнительные поля
    karma = models.IntegerField(default=0, verbose_name='Карма')
    cake_day = models.DateTimeField(auto_now_add=True, verbose_name='День регистрации')
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse('users:profile', kwargs={'username': self.username})


class UserProfile(models.Model):
    """
    Профиль пользователя с дополнительной информацией.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,  # При удалении пользователя удалится и профиль
        related_name='profile'
    )
    avatar = models.ImageField(
        upload_to='avatars/',  # Картинки сохранятся в папку media/avatars/
        blank=True, 
        null=True,
        verbose_name='Аватар'
    )
    bio = models.TextField(
        max_length=500, 
        blank=True, 
        verbose_name='О себе'
    )
    # Настройки приватности
    show_email = models.BooleanField(default=False, verbose_name='Показывать email')
    nsfw_enabled = models.BooleanField(default=False, verbose_name='Показывать NSFW')
    
    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'
    
    def __str__(self):
        return f'Профиль {self.user.username}'
    
    @property
    def avatar_url(self):
        """
        Возвращает URL аватара или путь к заглушке.
        @property позволяет обращаться как к атрибуту, а не как к методу.
        """
        if self.avatar:
            return self.avatar.url
        return '/static/default-avatar.png'


class UserFollow(models.Model):
    """
    Подписки пользователей друг на друга.
    """
    follower = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='following'  # user.following — на кого подписан
    )
    following = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='followers'  # user.followers — кто подписан на него
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Запрещаем дублирующиеся подписки
        unique_together = ['follower', 'following']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
    
    def __str__(self):
        return f'{self.follower} → {self.following}'


class UserBlock(models.Model):
    """
    Блокировка пользователей.
    """
    blocker = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='blocked_users'
    )
    blocked = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='blocked_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['blocker', 'blocked']
        verbose_name = 'Блокировка'
        verbose_name_plural = 'Блокировки'
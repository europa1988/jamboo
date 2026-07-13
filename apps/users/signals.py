from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Автоматически создаём профиль при создании пользователя.
    post_save — сигнал, который срабатывает после сохранения модели.
    """
    if created:
        # Импортируем здесь, чтобы избежать циклического импорта
        from .models import UserProfile
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """
    Сохраняем профиль при сохранении пользователя.
    """
    # Профиль создаётся автоматически, но на всякий случай проверяем
    if hasattr(instance, 'profile'):
        instance.profile.save()
from django.db import models
from django.conf import settings


class MediaFile(models.Model):
    """
    Загруженный файл (изображение, видео).
    """
    FILE_TYPES = [
        ('image', 'Изображение'),
        ('video', 'Видео'),
        ('gif', 'GIF'),
    ]
    
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    original_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    mime_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField(help_text='Размер в байтах')
    
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploads'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Медиафайл'
        verbose_name_plural = 'Медиафайлы'
    
    def __str__(self):
        return self.original_name
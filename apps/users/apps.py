from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'Пользователи'
    
    def ready(self):
        """
        Метод вызывается при запуске Django.
        Здесь подключаем сигналы.
        """
        import apps.users.signals  # Импортируем сигналы
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile, UserFollow, UserBlock


class UserProfileInline(admin.StackedInline):
    """
    Профиль отображается на странице пользователя.
    """
    model = UserProfile
    can_delete = False


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Кастомная админка для пользователей.
    """
    list_display = ['username', 'email', 'karma', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_active', 'date_joined']
    search_fields = ['username', 'email']
    inlines = [UserProfileInline]
    
    # Добавляем karma в поля редактирования
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('karma',)}),
    )


@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']
    list_filter = ['created_at']


@admin.register(UserBlock)
class UserBlockAdmin(admin.ModelAdmin):
    list_display = ['blocker', 'blocked', 'created_at']
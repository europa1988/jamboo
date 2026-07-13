from django.contrib import admin
from .models import ModLog, Report, RemovalReason


@admin.register(ModLog)
class ModLogAdmin(admin.ModelAdmin):
    list_display = ['community', 'moderator', 'action', 'created_at']
    list_filter = ['action', 'created_at']
    date_hierarchy = 'created_at'


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'reason', 'status', 'created_at']
    list_filter = ['status', 'reason', 'created_at']


@admin.register(RemovalReason)
class RemovalReasonAdmin(admin.ModelAdmin):
    list_display = ['community', 'title']
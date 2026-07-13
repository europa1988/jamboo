from django.contrib import admin
from .models import Community, CommunityMember, CommunityRule, CommunityBan


class CommunityMemberInline(admin.TabularInline):
    model = CommunityMember
    extra = 1


class CommunityRuleInline(admin.TabularInline):
    model = CommunityRule
    extra = 1


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ['name', 'community_type', 'member_count', 'created_at']
    list_filter = ['community_type', 'created_at']
    search_fields = ['name', 'description']
    inlines = [CommunityMemberInline, CommunityRuleInline]


@admin.register(CommunityBan)
class CommunityBanAdmin(admin.ModelAdmin):
    list_display = ['user', 'community', 'banned_by', 'created_at']
    list_filter = ['community', 'created_at']
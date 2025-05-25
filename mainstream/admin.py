from django.contrib import admin
from .models import MainstreamProfile

@admin.register(MainstreamProfile)
class MainstreamProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_username', 'relationship_status', 'looking_for', 'education_level', 'created_at')
    list_filter = ('relationship_status', 'looking_for', 'education_level', 'created_at')
    search_fields = ('profile__user__username', 'profile__user__email', 'occupation')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_username(self, obj):
        return obj.profile.user.username
    get_username.short_description = 'Username'
    get_username.admin_order_field = 'profile__user__username'

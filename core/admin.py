from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import Profile, Interest, Match, Like, Block, Report


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user_display', 'gender', 'age', 'location', 'created_at', 'profile_completion')
    list_filter = ('gender', 'created_at')
    search_fields = ('user__username', 'user__email', 'location')
    readonly_fields = ('created_at', 'updated_at', 'last_location_update')
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'bio', 'birth_date', 'gender', 'location')
        }),
        ('Profile Media', {
            'fields': ('profile_picture',)
        }),
        ('Location Data', {
            'fields': ('latitude', 'longitude', 'last_location_update')
        }),
        ('Preferences', {
            'fields': ('min_age_preference', 'max_age_preference', 'distance_preference')
        }),
        ('Notifications', {
            'fields': ('receive_message_notifications', 'receive_match_notifications', 'receive_like_notifications', 'fcm_token')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def user_display(self, obj):
        return f"{obj.user.username} ({obj.user.email})"
    user_display.short_description = 'User'
    
    def profile_completion(self, obj):
        # Calculate profile completion percentage
        fields = [
            bool(obj.user.first_name and obj.user.last_name),
            bool(obj.birth_date),
            bool(obj.gender),
            bool(obj.bio),
            bool(obj.profile_picture),
            bool(obj.location),
            bool(obj.latitude and obj.longitude),
            bool(obj.interests.all()),
        ]
        completion = sum(1 for field in fields if field) / len(fields) * 100
        
        # Color based on completion percentage
        if completion < 50:
            color = 'red'
        elif completion < 80:
            color = 'orange'
        else:
            color = 'green'
        
        return format_html(
            '<div style="width:100%%; background-color: #f0f0f0; height: 15px; border-radius: 5px;">'
            '<div style="width: {}%%; background-color: {}; height: 15px; border-radius: 5px;"></div>'
            '</div>'
            '<span>{:.0f}%</span>',
            completion, color, completion
        )
    profile_completion.short_description = 'Completion'


@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'user_count')
    list_filter = ('category',)
    search_fields = ('name', 'category')
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            user_count=Count('profile')
        )
        return queryset
    
    def user_count(self, obj):
        return obj.user_count
    user_count.admin_order_field = 'user_count'
    user_count.short_description = 'Users'


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('match_display', 'created_at', 'has_messages')
    list_filter = ('created_at',)
    search_fields = ('user1__username', 'user2__username')
    date_hierarchy = 'created_at'
    
    def match_display(self, obj):
        return f"{obj.user1.username} & {obj.user2.username}"
    match_display.short_description = 'Match'
    
    def has_messages(self, obj):
        # Check if there are any messages between these users
        from messaging.models import Message
        message_count = Message.objects.filter(
            sender__in=[obj.user1, obj.user2],
            receiver__in=[obj.user1, obj.user2]
        ).count()
        
        if message_count > 0:
            return format_html('<span style="color: green;">✓</span> ({} messages)', message_count)
        return format_html('<span style="color: red;">✗</span>')
    has_messages.short_description = 'Conversation Started'


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'created_at', 'resulted_in_match')
    list_filter = ('created_at',)
    search_fields = ('from_user__username', 'to_user__username')
    date_hierarchy = 'created_at'
    
    def resulted_in_match(self, obj):
        # Check if this like resulted in a match
        mutual_like = Like.objects.filter(
            from_user=obj.to_user,
            to_user=obj.from_user
        ).exists()
        
        if mutual_like:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    resulted_in_match.short_description = 'Match'


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'created_at', 'reason')
    list_filter = ('created_at',)
    search_fields = ('from_user__username', 'to_user__username', 'reason')
    date_hierarchy = 'created_at'


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'against_user', 'report_type', 'created_at', 'is_resolved')
    list_filter = ('report_type', 'is_resolved', 'created_at')
    search_fields = ('from_user__username', 'against_user__username', 'details')
    date_hierarchy = 'created_at'
    actions = ['mark_as_resolved', 'mark_as_unresolved']
    
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(is_resolved=True)
        self.message_user(request, f"{updated} reports marked as resolved.")
    mark_as_resolved.short_description = "Mark selected reports as resolved"
    
    def mark_as_unresolved(self, request, queryset):
        updated = queryset.update(is_resolved=False)
        self.message_user(request, f"{updated} reports marked as unresolved.")
    mark_as_unresolved.short_description = "Mark selected reports as unresolved"


# Custom admin site header and title
admin.site.site_header = "Super Dating App Administration"
admin.site.site_title = "Super Dating App Admin"
admin.site.index_title = "Welcome to Super Dating App Admin"

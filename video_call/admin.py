from django.contrib import admin
from .models import CallSession, CallFeedback

@admin.register(CallSession)
class CallSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'caller', 'receiver', 'call_type', 'status', 'started_at', 'duration')
    list_filter = ('call_type', 'status')
    search_fields = ('caller__username', 'receiver__username')
    date_hierarchy = 'started_at'

@admin.register(CallFeedback)
class CallFeedbackAdmin(admin.ModelAdmin):
    list_display = ('call_session', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('user__username', 'comments') 
from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('conversation/<int:conversation_id>/', views.conversation_view, name='conversation_detail'),
    path('conversation/<int:conversation_id>/delete/', views.delete_conversation, name='delete_conversation'),
    path('start/<str:username>/', views.start_conversation, name='start_conversation'),
    path('refresh/', views.inbox_refresh, name='inbox_refresh'),
    
    # Notification URLs
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('notifications/count/', views.notification_count, name='notification_count'),
] 
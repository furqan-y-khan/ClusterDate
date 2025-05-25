from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import CallSession
from messaging.models import Notification
from django.utils import timezone
from core.utils import send_call_notification

@receiver(post_save, sender=CallSession)
def create_call_notification(sender, instance, created, **kwargs):
    """
    Create a notification when a call is initiated, accepted, rejected, or missed
    """
    if created:
        # New call initiated - notify the receiver
        Notification.objects.create(
            user=instance.receiver,
            notification_type='CALL',
            content=f"{instance.caller.username} is calling you ({instance.call_type.lower()} call)",
            related_user=instance.caller
        )
        
        # Send push notification
        send_call_notification(instance)
        
    elif instance.status == 'COMPLETED':
        # Call completed - notify both users
        duration_mins = instance.duration // 60
        duration_secs = instance.duration % 60
        
        # Notify caller
        Notification.objects.create(
            user=instance.caller,
            notification_type='SYSTEM',
            content=f"Your call with {instance.receiver.username} has ended. Duration: {duration_mins}m {duration_secs}s",
            related_user=instance.receiver
        )
        
        # Notify receiver
        Notification.objects.create(
            user=instance.receiver,
            notification_type='SYSTEM',
            content=f"Your call with {instance.caller.username} has ended. Duration: {duration_mins}m {duration_secs}s",
            related_user=instance.caller
        )
    elif instance.status == 'REJECTED':
        # Call rejected - notify the caller
        Notification.objects.create(
            user=instance.caller,
            notification_type='SYSTEM',
            content=f"{instance.receiver.username} rejected your call",
            related_user=instance.receiver
        )
    elif instance.status == 'MISSED':
        # Call missed - notify the caller
        Notification.objects.create(
            user=instance.caller,
            notification_type='SYSTEM',
            content=f"{instance.receiver.username} missed your call",
            related_user=instance.receiver
        )
        
        # Notify the receiver about the missed call
        Notification.objects.create(
            user=instance.receiver,
            notification_type='SYSTEM',
            content=f"You missed a call from {instance.caller.username}",
            related_user=instance.caller
        ) 
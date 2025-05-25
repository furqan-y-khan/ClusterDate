from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message, Notification
from core.utils import send_message_notification

@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    """
    Create a notification when a new message is received
    """
    if created:
        # Get the receiver (other participant)
        receiver = instance.conversation.get_other_participant(instance.sender)
        
        if receiver:
            # Create database notification
            Notification.objects.create(
                user=receiver,
                notification_type='MESSAGE',
                content=f"New message from {instance.sender.username}",
                related_user=instance.sender,
                related_conversation=instance.conversation
            )
            
            # Send push notification
            send_message_notification(instance) 
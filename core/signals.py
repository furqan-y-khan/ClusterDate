from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Match, Like, Profile
from django.contrib.auth.models import User
from django.utils import timezone
from messaging.models import Notification
from .utils import send_match_notification, send_like_notification

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to create a profile when a new user is created
    """
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=Like)
def handle_new_like(sender, instance, created, **kwargs):
    """
    Signal to handle new likes and create matches if mutual
    """
    if created:
        # Check for mutual like and create match if found
        instance.create_match_if_mutual()

@receiver(post_save, sender=Match)
def handle_new_match(sender, instance, created, **kwargs):
    """
    Signal to handle new matches
    """
    if created:
        # Send notifications to both users
        from django.contrib.auth.models import User
        
        # Notify user1
        if hasattr(instance.user1, 'profile') and instance.user1.profile.receive_match_notifications:
            try:
                from notifications.signals import notify
                notify.send(
                    sender=instance.user2,
                    recipient=instance.user1,
                    verb='matched with you',
                    target=instance,
                    description=f"You have a new match with {instance.user2.username}!"
                )
            except ImportError:
                # Notifications app not available
                pass
        
        # Notify user2
        if hasattr(instance.user2, 'profile') and instance.user2.profile.receive_match_notifications:
            try:
                from notifications.signals import notify
                notify.send(
                    sender=instance.user1,
                    recipient=instance.user2,
                    verb='matched with you',
                    target=instance,
                    description=f"You have a new match with {instance.user1.username}!"
                )
            except ImportError:
                # Notifications app not available
                pass

@receiver(post_save, sender=Match)
def notify_match(sender, instance, created, **kwargs):
    """
    Send notifications when a match is created
    """
    if created: # Removed instance.is_mutual check
        # Create database notifications
        Notification.objects.create(
            user=instance.user1,
            notification_type='MATCH',
            content=f"You matched with {instance.user2.username}!",
            related_user=instance.user2
        )
        
        Notification.objects.create(
            user=instance.user2,
            notification_type='MATCH',
            content=f"You matched with {instance.user1.username}!",
            related_user=instance.user1
        )
        
        # Send push notifications
        send_match_notification(instance)

@receiver(post_save, sender=Like)
def notify_like(sender, instance, created, **kwargs):
    """
    Send notification when a like is created
    """
    if created:
        # Create database notification
        Notification.objects.create(
            user=instance.to_user,
            notification_type='LIKE',
            content=f"{instance.from_user.username} liked your profile!",
            related_user=instance.from_user
        )
        
        # Send push notification
        send_like_notification(instance)
        
        # Check if this like created a match
        reverse_like = Like.objects.filter(
            from_user=instance.to_user,
            to_user=instance.from_user
        ).first()
        
        if reverse_like:
            # Create a match, ensuring user1.id < user2.id for consistency
            if instance.from_user.id < instance.to_user.id:
                user1, user2 = instance.from_user, instance.to_user
            else:
                user1, user2 = instance.to_user, instance.from_user
            Match.objects.get_or_create(user1=user1, user2=user2)
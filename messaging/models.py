from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Conversation(models.Model):
    """
    Model to represent a conversation between two users
    """
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Conversation {self.id}"
    
    def get_other_participant(self, user):
        """Get the other participant in a two-person conversation"""
        return self.participants.exclude(id=user.id).first()
    
    def get_last_message(self):
        """Get the last message in the conversation"""
        return self.messages.order_by('-created_at').first()


class Message(models.Model):
    """
    Model to represent a message within a conversation
    """
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # For ephemeral messages (used in casual dating)
    is_ephemeral = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Message from {self.sender.username} in conversation {self.conversation.id}"
    
    def mark_as_read(self):
        """Mark the message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def is_expired(self):
        """Check if an ephemeral message has expired"""
        if self.is_ephemeral and self.expires_at:
            return timezone.now() > self.expires_at
        return False


class Notification(models.Model):
    """
    Model to store notifications for users
    """
    NOTIFICATION_TYPES = (
        ('MESSAGE', 'New Message'),
        ('MATCH', 'New Match'),
        ('LIKE', 'New Like'),
        ('SYSTEM', 'System Notification'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES)
    content = models.TextField()
    related_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications_as_subject')
    related_conversation = models.ForeignKey(Conversation, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.notification_type} notification for {self.user.username}"

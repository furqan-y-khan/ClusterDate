from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class CallSession(models.Model):
    """
    Model to represent a video/audio call session between users
    """
    CALL_TYPES = (
        ('AUDIO', 'Audio Call'),
        ('VIDEO', 'Video Call'),
    )
    
    CALL_STATUS = (
        ('REQUESTED', 'Requested'),
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
        ('MISSED', 'Missed'),
        ('REJECTED', 'Rejected'),
    )
    
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    caller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calls_initiated')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calls_received')
    call_type = models.CharField(max_length=10, choices=CALL_TYPES, default='VIDEO')
    status = models.CharField(max_length=10, choices=CALL_STATUS, default='REQUESTED')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(default=0)  # Duration in seconds
    
    def __str__(self):
        return f"{self.call_type} call from {self.caller.username} to {self.receiver.username}"
    
    def end_call(self):
        """End the call and calculate duration"""
        if self.status == 'ONGOING':
            self.status = 'COMPLETED'
            self.ended_at = timezone.now()
            if self.started_at:
                # Calculate duration in seconds
                duration = (self.ended_at - self.started_at).total_seconds()
                self.duration = int(duration)
            self.save()
    
    def accept_call(self):
        """Accept the call"""
        if self.status == 'REQUESTED':
            self.status = 'ONGOING'
            self.save()
    
    def reject_call(self):
        """Reject the call"""
        if self.status == 'REQUESTED':
            self.status = 'REJECTED'
            self.ended_at = timezone.now()
            self.save()
    
    def mark_as_missed(self):
        """Mark the call as missed"""
        if self.status == 'REQUESTED':
            self.status = 'MISSED'
            self.ended_at = timezone.now()
            self.save()


class CallFeedback(models.Model):
    """
    Model to store feedback about call quality
    """
    RATING_CHOICES = (
        (1, 'Very Poor'),
        (2, 'Poor'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent'),
    )
    
    call_session = models.ForeignKey(CallSession, on_delete=models.CASCADE, related_name='feedback')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    audio_quality = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    video_quality = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    connection_stability = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Feedback from {self.user.username} for call {self.call_session.id}" 
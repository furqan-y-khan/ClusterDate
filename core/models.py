from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import math

class Profile(models.Model):
    """
    Core profile model that extends the User model with additional fields.
    This is shared across all dating categories.
    """
    GENDER_CHOICES = (
        ('M', _('Male')),
        ('F', _('Female')),
        ('NB', _('Non-Binary')),
        ('O', _('Other')),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=2, choices=GENDER_CHOICES, blank=True)
    location = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    interests = models.ManyToManyField('Interest', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Location fields for Google Maps
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)
    
    # Matching preferences
    min_age_preference = models.IntegerField(default=18)
    max_age_preference = models.IntegerField(default=100)
    distance_preference = models.IntegerField(default=50)  # in miles/km
    
    # Notification preferences
    receive_message_notifications = models.BooleanField(default=True)
    receive_match_notifications = models.BooleanField(default=True)
    receive_like_notifications = models.BooleanField(default=True)
    
    # Firebase Cloud Messaging token for push notifications
    fcm_token = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    @property
    def age(self):
        """Calculate age based on birth_date"""
        from datetime import date
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None
        
    def update_location(self, latitude, longitude):
        """Update the user's location"""
        self.latitude = latitude
        self.longitude = longitude
        self.last_location_update = timezone.now()
        self.save()
        
    def distance_to(self, other_profile):
        """Calculate distance to another profile in kilometers"""
        if not self.latitude or not self.longitude or not other_profile.latitude or not other_profile.longitude:
            return None
            
        # Haversine formula
        lon1, lat1, lon2, lat2 = map(math.radians, [self.longitude, self.latitude, 
                                              other_profile.longitude, other_profile.latitude])
        
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Radius of Earth in kilometers
        
        return c * r


class Interest(models.Model):
    """
    Model to store interests/hobbies that users can select
    """
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return self.name


class Match(models.Model):
    """
    Model to store matches between users
    """
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_as_user2')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user1', 'user2')
    
    def __str__(self):
        return f"Match between {self.user1.username} and {self.user2.username}"


class Like(models.Model):
    """
    Model to store likes between users
    """
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_sent')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_received')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('from_user', 'to_user')
    
    def __str__(self):
        return f"{self.from_user.username} likes {self.to_user.username}"
    
    def create_match_if_mutual(self):
        """
        Check if there's a mutual like and create a match if so
        """
        mutual_like = Like.objects.filter(
            from_user=self.to_user,
            to_user=self.from_user
        ).exists()
        
        if mutual_like:
            # Create a match (ensure user1 is always the lower ID for consistency)
            if self.from_user.id < self.to_user.id:
                user1, user2 = self.from_user, self.to_user
            else:
                user1, user2 = self.to_user, self.from_user
                
            Match.objects.get_or_create(user1=user1, user2=user2)
            return True
        
        return False


class Block(models.Model):
    """
    Model to store blocked users
    """
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocks_sent')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocks_received')
    created_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('from_user', 'to_user')
    
    def __str__(self):
        return f"{self.from_user.username} blocked {self.to_user.username}"


class Report(models.Model):
    """
    Model to store user reports
    """
    REPORT_TYPES = (
        ('FAKE', _('Fake Profile')),
        ('INAPPROPRIATE', _('Inappropriate Content')),
        ('HARASSMENT', _('Harassment')),
        ('OTHER', _('Other')),
    )
    
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_sent')
    against_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Report by {self.from_user.username} against {self.against_user.username}"


class MatchRequest(models.Model):
    """
    Represents a match request from one user to another
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined'),
    )
    
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_match_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_match_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('from_user', 'to_user')
    
    def __str__(self):
        return f"Match request from {self.from_user.username} to {self.to_user.username} ({self.status})"


class Notification(models.Model):
    """
    Represents a notification for a user
    """
    TYPE_CHOICES = (
        ('LIKE', 'Like'),
        ('MATCH', 'Match'),
        ('MATCH_REQUEST', 'Match Request'),
        ('MESSAGE', 'Message'),
        ('SYSTEM', 'System'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='core_notifications')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    content = models.TextField()
    related_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='related_core_notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user.username}: {self.notification_type}"

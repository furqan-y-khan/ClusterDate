from django.db import models
from django.contrib.auth.models import User
from core.models import Profile

class SugarProfile(models.Model):
    """
    Extended profile for sugar dating with specific fields
    """
    INCOME_RANGES = (
        ('1', 'Under $50,000'),
        ('2', '$50,000 - $100,000'),
        ('3', '$100,000 - $250,000'),
        ('4', '$250,000 - $500,000'),
        ('5', '$500,000 - $1,000,000'),
        ('6', 'Over $1,000,000'),
        ('7', 'Prefer not to say'),
    )
    
    LIFESTYLE_CHOICES = (
        ('MODEST', 'Modest'),
        ('COMFORTABLE', 'Comfortable'),
        ('WEALTHY', 'Wealthy'),
        ('LUXURIOUS', 'Luxurious'),
    )
    
    RELATIONSHIP_EXPECTATIONS = (
        ('PLATONIC', 'Platonic'),
        ('ROMANTIC', 'Romantic'),
        ('MENTORSHIP', 'Mentorship'),
        ('TRAVEL', 'Travel Partner'),
        ('FLEXIBLE', 'Flexible'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='sugar_profile')
    is_sugar_daddy = models.BooleanField(default=False)
    is_sugar_mommy = models.BooleanField(default=False)
    is_sugar_baby = models.BooleanField(default=False)
    
    # Financial information (for sugar daddies/mommies)
    income_range = models.CharField(max_length=1, choices=INCOME_RANGES, blank=True)
    net_worth_range = models.CharField(max_length=1, choices=INCOME_RANGES, blank=True)
    is_income_verified = models.BooleanField(default=False)
    lifestyle = models.CharField(max_length=15, choices=LIFESTYLE_CHOICES, blank=True)
    
    # Expectations
    relationship_type = models.CharField(max_length=15, choices=RELATIONSHIP_EXPECTATIONS, blank=True)
    allowance_expectations = models.TextField(blank=True)
    travel_preferences = models.TextField(blank=True)
    
    # Verification
    is_background_checked = models.BooleanField(default=False)
    background_check_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        role = "Sugar Daddy" if self.is_sugar_daddy else "Sugar Mommy" if self.is_sugar_mommy else "Sugar Baby"
        return f"{self.user.username}'s {role} Profile"


class IncomeVerification(models.Model):
    """
    Model to store income verification documents
    """
    VERIFICATION_STATUS = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='income_verification')
    document = models.FileField(upload_to='income_verification/')
    status = models.CharField(max_length=10, choices=VERIFICATION_STATUS, default='PENDING')
    submitted_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Income verification for {self.user.username} - {self.status}"


class LuxuryEvent(models.Model):
    """
    Model for luxury events that premium users can attend
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    date = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='events/', null=True, blank=True)
    is_exclusive = models.BooleanField(default=True)
    max_attendees = models.IntegerField(default=50)
    
    # Relationships
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')
    attendees = models.ManyToManyField(User, related_name='attending_events', through='EventAttendee')
    
    def __str__(self):
        return self.title


class EventAttendee(models.Model):
    """
    Model to track event attendees
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(LuxuryEvent, on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)
    has_paid = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'event')
    
    def __str__(self):
        return f"{self.user.username} attending {self.event.title}"

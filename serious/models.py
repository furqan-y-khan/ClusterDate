from django.db import models
from django.contrib.auth.models import User
from core.models import Profile

class SeriousProfile(models.Model):
    """
    Extended profile for serious relationship dating with specific fields
    """
    RELATIONSHIP_GOALS_CHOICES = (
        ('DATING', 'Dating'),
        ('RELATIONSHIP', 'Serious Relationship'),
        ('MARRIAGE', 'Marriage'),
        ('FAMILY', 'Starting a Family'),
    )
    
    RELATIONSHIP_TYPE_CHOICES = (
        ('MONOGAMOUS', 'Monogamous'),
        ('POLYAMOROUS', 'Polyamorous'),
        ('OPEN', 'Open Relationship'),
    )
    
    EDUCATION_LEVEL_CHOICES = (
        ('HIGH_SCHOOL', 'High School'),
        ('ASSOCIATES', 'Associate\'s Degree'),
        ('BACHELORS', 'Bachelor\'s Degree'),
        ('MASTERS', 'Master\'s Degree'),
        ('DOCTORATE', 'Doctorate or Higher'),
        ('OTHER', 'Other'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='serious_profile')
    
    # Basic information
    about_me = models.TextField(blank=True, help_text="Tell others about yourself")
    looking_for = models.TextField(blank=True, help_text="Describe what you're looking for in a partner")
    
    # Relationship preferences
    relationship_goals = models.CharField(max_length=20, choices=RELATIONSHIP_GOALS_CHOICES, blank=True)
    relationship_type = models.CharField(max_length=20, choices=RELATIONSHIP_TYPE_CHOICES, blank=True)
    want_children = models.BooleanField(null=True, blank=True, help_text="Do you want children?")
    have_children = models.BooleanField(null=True, blank=True, help_text="Do you have children?")
    
    # Personal attributes
    smoking = models.BooleanField(null=True, blank=True, help_text="Do you smoke?")
    drinking = models.CharField(max_length=20, choices=(
        ('NEVER', 'Never'),
        ('RARELY', 'Rarely'),
        ('SOCIALLY', 'Socially'),
        ('REGULARLY', 'Regularly'),
    ), blank=True)
    
    # Education and career
    education = models.CharField(max_length=20, choices=EDUCATION_LEVEL_CHOICES, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    
    # Deal breakers and preferences
    deal_breakers = models.TextField(blank=True, help_text="What are your relationship deal breakers?")
    
    # Verification fields
    is_identity_verified = models.BooleanField(default=False)
    is_background_checked = models.BooleanField(default=False)
    verified_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Serious Dating Profile"

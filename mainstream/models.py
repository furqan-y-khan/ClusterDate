from django.db import models
from django.contrib.auth.models import User
from core.models import Profile

class MainstreamProfile(models.Model):
    """
    Extended profile model specific to the mainstream dating app
    """
    RELATIONSHIP_STATUS_CHOICES = (
        ('SINGLE', 'Single'),
        ('DIVORCED', 'Divorced'),
        ('SEPARATED', 'Separated'),
        ('WIDOWED', 'Widowed'),
    )

    LOOKING_FOR_CHOICES = (
        ('DATING', 'Dating'),
        ('RELATIONSHIP', 'Relationship'),
        ('FRIENDSHIP', 'Friendship'),
        ('MARRIAGE', 'Marriage'),
    )

    EDUCATION_LEVEL_CHOICES = (
        ('HIGH_SCHOOL', 'High School'),
        ('COLLEGE', 'College'),
        ('BACHELORS', 'Bachelor\'s Degree'),
        ('MASTERS', 'Master\'s Degree'),
        ('DOCTORATE', 'Doctorate'),
    )

    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='mainstream_profile')
    
    # Additional mainstream-specific fields
    relationship_status = models.CharField(max_length=10, choices=RELATIONSHIP_STATUS_CHOICES, blank=True)
    looking_for = models.CharField(max_length=12, choices=LOOKING_FOR_CHOICES, blank=True)
    education_level = models.CharField(max_length=15, choices=EDUCATION_LEVEL_CHOICES, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    
    # Matching preferences
    interested_in_gender = models.CharField(max_length=10, blank=True)
    
    # Advanced preferences
    has_children = models.BooleanField(null=True, blank=True)
    wants_children = models.BooleanField(null=True, blank=True)
    smoker = models.BooleanField(null=True, blank=True)
    drinker = models.BooleanField(null=True, blank=True)
    
    # Additional photos
    photo_1 = models.ImageField(upload_to='mainstream/photos/', blank=True, null=True)
    photo_2 = models.ImageField(upload_to='mainstream/photos/', blank=True, null=True)
    photo_3 = models.ImageField(upload_to='mainstream/photos/', blank=True, null=True)
    photo_4 = models.ImageField(upload_to='mainstream/photos/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.profile.user.username}'s Mainstream Profile"

    def get_match_score(self, other_profile):
        """
        Calculate a match score between this profile and another profile
        Higher score means better match
        """
        score = 0
        
        # Basic compatibility checks
        if self.interested_in_gender == other_profile.profile.gender:
            score += 20
            
        # Check for mutual interests
        user1_interests = set(self.profile.interests.all().values_list('id', flat=True))
        user2_interests = set(other_profile.profile.interests.all().values_list('id', flat=True))
        common_interests = user1_interests.intersection(user2_interests)
        score += len(common_interests) * 5
        
        # Check age preferences
        if other_profile.profile.age:
            if (self.profile.min_age_preference <= other_profile.profile.age <= 
                self.profile.max_age_preference):
                score += 15
                
        # Check distance preferences if location data is available
        distance = self.profile.distance_to(other_profile.profile)
        if distance is not None:
            if distance <= self.profile.distance_preference:
                distance_score = max(0, 20 - int(distance / 5))  # Closer is better
                score += distance_score
                
        # Check relationship compatibility
        if self.looking_for == other_profile.looking_for:
            score += 10
            
        return score

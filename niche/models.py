from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from core.models import Profile

class Community(models.Model):
    """
    Model for niche interest communities
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField()
    icon_class = models.CharField(max_length=50, default="fas fa-users", help_text="FontAwesome icon class")
    cover_image = models.ImageField(upload_to='community_covers/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True)
    suggested_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='suggested_communities')
    member_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name_plural = "Communities"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def update_member_count(self):
        self.member_count = self.profiles.count()
        self.save(update_fields=['member_count'])


class NicheProfile(models.Model):
    """
    Extended profile for niche dating with specific fields
    """
    EXPERIENCE_LEVEL_CHOICES = (
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced'),
        ('EXPERT', 'Expert'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='niche_profile')
    
    # Basic niche information
    communities = models.ManyToManyField(Community, related_name='profiles', blank=True)
    primary_interest = models.CharField(max_length=100, blank=True, help_text="Your main interest or passion")
    experience_level = models.CharField(max_length=15, choices=EXPERIENCE_LEVEL_CHOICES, blank=True)
    interest_description = models.TextField(blank=True, help_text="Describe your interest in more detail")
    
    # Preferences
    seeking_experience_levels = models.CharField(max_length=255, blank=True, help_text="Experience levels you're interested in (comma-separated)")
    interest_based_preferences = models.TextField(blank=True, help_text="What are you looking for in a match based on interests?")
    
    # Social media and external profiles
    social_media_links = models.JSONField(blank=True, null=True, default=dict, help_text="Links to your social profiles related to your interests")
    
    # Privacy settings
    show_experience_level = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Niche Dating Profile"
    
    def get_primary_community(self):
        """Get the user's primary community if any"""
        return self.communities.first()

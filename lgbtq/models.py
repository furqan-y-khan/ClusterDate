from django.db import models
from django.contrib.auth.models import User
from core.models import Profile

class LGBTQProfile(models.Model):
    """
    Extended profile for LGBTQ+ dating with specific fields
    """
    GENDER_IDENTITY_CHOICES = (
        ('CIS_MALE', 'Cisgender Male'),
        ('CIS_FEMALE', 'Cisgender Female'),
        ('TRANS_MALE', 'Transgender Male'),
        ('TRANS_FEMALE', 'Transgender Female'),
        ('NON_BINARY', 'Non-Binary'),
        ('GENDERFLUID', 'Genderfluid'),
        ('GENDERQUEER', 'Genderqueer'),
        ('AGENDER', 'Agender'),
        ('OTHER', 'Other'),
    )
    
    SEXUAL_ORIENTATION_CHOICES = (
        ('GAY', 'Gay'),
        ('LESBIAN', 'Lesbian'),
        ('BISEXUAL', 'Bisexual'),
        ('PANSEXUAL', 'Pansexual'),
        ('ASEXUAL', 'Asexual'),
        ('DEMISEXUAL', 'Demisexual'),
        ('QUEER', 'Queer'),
        ('QUESTIONING', 'Questioning'),
        ('OTHER', 'Other'),
    )
    
    PRONOUNS_CHOICES = (
        ('HE_HIM', 'He/Him'),
        ('SHE_HER', 'She/Her'),
        ('THEY_THEM', 'They/Them'),
        ('ZE_HIR', 'Ze/Hir'),
        ('XE_XEM', 'Xe/Xem'),
        ('CUSTOM', 'Custom'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lgbtq_profile')
    gender_identity = models.CharField(max_length=15, choices=GENDER_IDENTITY_CHOICES, blank=True)
    sexual_orientation = models.CharField(max_length=15, choices=SEXUAL_ORIENTATION_CHOICES, blank=True)
    pronouns = models.CharField(max_length=10, choices=PRONOUNS_CHOICES, blank=True)
    custom_pronouns = models.CharField(max_length=50, blank=True)
    is_out = models.BooleanField(default=True)  # Whether the user is out publicly
    coming_out_story = models.TextField(blank=True)
    
    # Community involvement
    is_community_member = models.BooleanField(default=False)
    community_roles = models.TextField(blank=True)
    
    # Dating preferences specific to LGBTQ+
    open_to_dating_trans = models.BooleanField(default=True)
    open_to_dating_non_binary = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.username}'s LGBTQ+ Profile"


class CommunityEvent(models.Model):
    """
    Model for LGBTQ+ community events
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    date = models.DateTimeField()
    image = models.ImageField(upload_to='lgbtq_events/', null=True, blank=True)
    is_private = models.BooleanField(default=False)
    
    # Event type
    is_pride = models.BooleanField(default=False)
    is_support_group = models.BooleanField(default=False)
    is_social = models.BooleanField(default=False)
    is_educational = models.BooleanField(default=False)
    
    # Relationships
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_lgbtq_events')
    attendees = models.ManyToManyField(User, related_name='attending_lgbtq_events')
    
    def __str__(self):
        return self.title


class CommunityResource(models.Model):
    """
    Model for LGBTQ+ community resources
    """
    RESOURCE_TYPES = (
        ('ARTICLE', 'Article'),
        ('VIDEO', 'Video'),
        ('PODCAST', 'Podcast'),
        ('ORGANIZATION', 'Organization'),
        ('SUPPORT', 'Support Service'),
        ('LEGAL', 'Legal Resource'),
        ('HEALTH', 'Health Resource'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    resource_type = models.CharField(max_length=15, choices=RESOURCE_TYPES)
    url = models.URLField()
    image = models.ImageField(upload_to='lgbtq_resources/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Content tags
    is_for_youth = models.BooleanField(default=False)
    is_for_trans = models.BooleanField(default=False)
    is_for_parents = models.BooleanField(default=False)
    is_for_allies = models.BooleanField(default=False)
    
    # Relationships
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='added_resources')
    
    def __str__(self):
        return self.title

from django.db import models
from django.contrib.auth.models import User
from core.models import Profile


class ReligionProfile(models.Model):
    """
    Additional profile fields specific to religion-based dating
    """
    RELIGION_CHOICES = (
        ('CH', 'Christianity'),
        ('IS', 'Islam'),
        ('HI', 'Hinduism'),
        ('BU', 'Buddhism'),
        ('JU', 'Judaism'),
        ('SI', 'Sikhism'),
        ('OT', 'Other'),
        ('NO', 'Non-religious/Spiritual'),
    )
    
    RELIGIOSITY_CHOICES = (
        (1, 'Not religious at all'),
        (2, 'Slightly religious'),
        (3, 'Moderately religious'),
        (4, 'Religious'),
        (5, 'Very religious'),
    )
    
    DENOMINATION_CHOICES = {
        'CH': [  # Christianity denominations
            ('CA', 'Catholic'),
            ('PR', 'Protestant'),
            ('OR', 'Orthodox'),
            ('EV', 'Evangelical'),
            ('OT', 'Other'),
        ],
        'IS': [  # Islam denominations
            ('SU', 'Sunni'),
            ('SH', 'Shia'),
            ('OT', 'Other'),
        ],
        'HI': [  # Hinduism denominations
            ('VA', 'Vaishnavism'),
            ('SH', 'Shaivism'),
            ('OT', 'Other'),
        ],
        'JU': [  # Judaism denominations
            ('OR', 'Orthodox'),
            ('CO', 'Conservative'),
            ('RE', 'Reform'),
            ('OT', 'Other'),
        ],
        'BU': [  # Buddhism denominations
            ('TH', 'Theravada'),
            ('MA', 'Mahayana'),
            ('VA', 'Vajrayana'),
            ('OT', 'Other'),
        ],
        'SI': [  # Sikhism denominations
            ('GE', 'General'),
            ('OT', 'Other'),
        ],
        'OT': [  # Other religions
            ('GE', 'General'),
        ],
        'NO': [  # Non-religious
            ('AG', 'Agnostic'),
            ('AT', 'Atheist'),
            ('SP', 'Spiritual but not religious'),
            ('OT', 'Other'),
        ],
    }
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='religion_profile')
    religion = models.CharField(max_length=2, choices=RELIGION_CHOICES)
    denomination = models.CharField(max_length=2, blank=True)
    religiosity = models.IntegerField(choices=RELIGIOSITY_CHOICES)
    practice_frequency = models.IntegerField(
        choices=(
            (1, 'Never'),
            (2, 'Only on special occasions'),
            (3, 'Monthly'),
            (4, 'Weekly'),
            (5, 'Daily')
        ),
        default=1
    )
    religious_values = models.TextField(
        help_text="Describe your religious beliefs and values",
        blank=True
    )
    
    # Preferences
    religion_preference = models.CharField(max_length=2, choices=RELIGION_CHOICES, blank=True)
    denomination_preference = models.CharField(max_length=2, blank=True)
    min_religiosity_preference = models.IntegerField(choices=RELIGIOSITY_CHOICES, default=1)
    max_religiosity_preference = models.IntegerField(choices=RELIGIOSITY_CHOICES, default=5)
    interfaith_willingness = models.BooleanField(
        default=True,
        help_text="Are you open to dating someone of a different faith?"
    )
    
    # Availability for religious activities
    available_for_worship = models.BooleanField(
        default=False,
        help_text="Available to attend worship services together"
    )
    available_for_prayer = models.BooleanField(
        default=False,
        help_text="Available for prayer or meditation together"
    )
    available_for_religious_study = models.BooleanField(
        default=False,
        help_text="Available for religious study together"
    )
    
    def __str__(self):
        return f"{self.user.username}'s Religion Profile"
    
    def get_religion_display_value(self):
        """Get the display value for the religion field"""
        for code, name in self.RELIGION_CHOICES:
            if code == self.religion:
                return name
        return "Unknown"
    
    def get_denomination_display_value(self):
        """Get the display value for the denomination field"""
        if not self.denomination or not self.religion:
            return ""
        
        for code, name in self.DENOMINATION_CHOICES.get(self.religion, []):
            if code == self.denomination:
                return name
        return "Other"
    
    def compatibility_score(self, other_profile):
        """
        Calculate religious compatibility score with another profile
        Returns a value between 0 and 1, where 1 is most compatible
        """
        score = 0.0
        
        # Check religion match
        if self.religion == other_profile.religion:
            score += 0.5
            
            # Check denomination match (if same religion)
            if self.denomination == other_profile.denomination:
                score += 0.2
        elif self.interfaith_willingness and other_profile.interfaith_willingness:
            # Some compatibility for interfaith matches
            score += 0.2
        else:
            # Not interfaith willing and different religions
            return 0.0
        
        # Check religiosity compatibility
        religiosity_diff = abs(self.religiosity - other_profile.religiosity)
        if religiosity_diff == 0:
            score += 0.3
        elif religiosity_diff == 1:
            score += 0.2
        elif religiosity_diff == 2:
            score += 0.1
        
        return min(1.0, score)

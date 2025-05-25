from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class Ethnicity(models.Model):
    """
    Model representing various ethnicities.
    """
    name = models.CharField(max_length=100, unique=True, help_text=_("Name of the ethnicity (e.g., Han Chinese, Yoruba, Andalusian)"))

    class Meta:
        verbose_name = _("Ethnicity")
        verbose_name_plural = _("Ethnicities")
        ordering = ['name']

    def __str__(self):
        return self.name

class Language(models.Model):
    """
    Model representing various languages.
    """
    name = models.CharField(max_length=100, unique=True, help_text=_("Name of the language (e.g., English, Mandarin, Spanish)"))

    class Meta:
        verbose_name = _("Language")
        verbose_name_plural = _("Languages")
        ordering = ['name']

    def __str__(self):
        return self.name

class EthnicProfile(models.Model):
    """
    Model to store ethnicity-specific profile details for a user.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='ethnic_profile',
        verbose_name=_("User")
    )
    ethnicities = models.ManyToManyField(
        Ethnicity, 
        blank=True, 
        verbose_name=_("Ethnicities"),
        help_text=_("Select one or more ethnicities that you identify with.")
    )
    home_country = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name=_("Home Country"),
        help_text=_("Country you consider home or grew up in.")
    )
    languages_spoken = models.ManyToManyField(
        Language, 
        blank=True, 
        verbose_name=_("Languages Spoken"),
        help_text=_("Languages you speak fluently.")
    )
    cultural_values_description = models.TextField(
        blank=True, 
        verbose_name=_("Cultural Values Description"),
        help_text=_("Briefly describe your cultural values or upbringing.")
    )
    partner_ethnicity_preference = models.ManyToManyField(
        Ethnicity, 
        related_name='preferred_by_ethnic_profiles', 
        blank=True, 
        verbose_name=_("Partner Ethnicity Preference"),
        help_text=_("Ethnicities you are interested in for a partner.")
    )
    partner_language_preference = models.ManyToManyField(
        Language, 
        related_name='preferred_by_ethnic_profiles_lang', 
        blank=True, 
        verbose_name=_("Partner Language Preference"),
        help_text=_("Languages you'd prefer your partner to speak.")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Ethnic Profile")
        verbose_name_plural = _("Ethnic Profiles")

    def __str__(self):
        return _(f"{self.user.username}'s Ethnic Profile")

# Consider adding a signal to create EthnicProfile when a User is created,
# similar to how the core Profile model might be handled.
# from django.db.models.signals import post_save
# from django.dispatch import receiver

# @receiver(post_save, sender=User)
# def create_user_ethnic_profile(sender, instance, created, **kwargs):
#     if created:
#         EthnicProfile.objects.create(user=instance)

# @receiver(post_save, sender=User)
# def save_user_ethnic_profile(sender, instance, **kwargs):
#     try:
#         instance.ethnic_profile.save()
#     except EthnicProfile.DoesNotExist:
#         # This might happen if the profile was deleted manually
#         # or if the user was created before this signal was in place.
#         EthnicProfile.objects.create(user=instance)

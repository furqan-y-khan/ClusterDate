from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class VerificationToken(models.Model):
    """
    Model to store verification tokens for email verification
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification_token')
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Verification token for {self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Token expires after 24 hours
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Check if the token is still valid"""
        return not self.is_used and timezone.now() < self.expires_at


class PasswordResetToken(models.Model):
    """
    Model to store password reset tokens
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='password_reset_token')
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Password reset token for {self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Token expires after 1 hour
            self.expires_at = timezone.now() + timezone.timedelta(hours=1)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Check if the token is still valid"""
        return not self.is_used and timezone.now() < self.expires_at


# IMPORTANT: The UserVerification model handles sensitive documents (ID and selfie).
# Ensure that the storage backend (e.g., S3 bucket policies) and media serving configuration
# in production restrict direct public access to the 'verification/id/' and 
# 'verification/selfie/' paths. Files should ideally be served via a view that
# checks user authentication and authorization.
class UserVerification(models.Model):
    """
    Model to store user verification status and documents
    Used for identity verification in premium categories like sugar dating
    """
    VERIFICATION_STATUS = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification')
    id_document = models.ImageField(upload_to='verification/id/', null=True, blank=True)
    selfie = models.ImageField(upload_to='verification/selfie/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=VERIFICATION_STATUS, default='PENDING')
    submitted_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    def clean(self):
        super().clean()
        MAX_UPLOAD_SIZE = 5 * 1024 * 1024 # 5MB
        if self.id_document and self.id_document.size > MAX_UPLOAD_SIZE:
            raise ValidationError(_(f'ID document file size cannot exceed {MAX_UPLOAD_SIZE // (1024*1024)}MB.'))
        if self.selfie and self.selfie.size > MAX_UPLOAD_SIZE:
            raise ValidationError(_(f'Selfie file size cannot exceed {MAX_UPLOAD_SIZE // (1024*1024)}MB.'))
    
    def __str__(self):
        return f"Verification for {self.user.username} - {self.status}"
    
    def approve(self):
        """Approve the verification"""
        self.status = 'APPROVED'
        self.verified_at = timezone.now()
        self.save()
    
    def reject(self, reason):
        """Reject the verification with a reason"""
        self.status = 'REJECTED'
        self.rejection_reason = reason
        self.save()

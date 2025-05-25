from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField


class Plan(models.Model):
    """
    Subscription plan model defining available subscription tiers
    """
    INTERVAL_CHOICES = (
        ('month', 'Monthly'),
        ('year', 'Yearly'),
    )
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    interval = models.CharField(max_length=10, choices=INTERVAL_CHOICES, default='month')
    stripe_price_id = models.CharField(max_length=100, blank=True)
    features = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} (${self.price}/{self.interval})"


class Subscription(models.Model):
    """
    User subscription model to track active subscriptions
    """
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('past_due', 'Past Due'),
        ('unpaid', 'Unpaid'),
        ('trialing', 'Trialing'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete Expired'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='incomplete')
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s {self.plan.name} subscription"
    
    @property
    def is_active(self):
        """Check if subscription is currently active"""
        return self.status == 'active' and (self.end_date is None or self.end_date > timezone.now())
    
    def cancel(self):
        """Mark subscription as canceled at period end"""
        self.cancel_at_period_end = True
        self.save()


class PaymentMethod(models.Model):
    """
    User payment method storage
    """
    TYPE_CHOICES = (
        ('card', 'Credit/Debit Card'),
        ('bank', 'Bank Account'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    stripe_payment_method_id = models.CharField(max_length=100)
    payment_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='card')
    last_4 = models.CharField(max_length=4)  # Last 4 digits of card or account
    expiry_month = models.IntegerField(null=True, blank=True)  # For cards
    expiry_year = models.IntegerField(null=True, blank=True)   # For cards
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_payment_type_display()} ending in {self.last_4}"


class Payment(models.Model):
    """
    Payment record for tracking all transactions
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True)
    stripe_charge_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    description = models.CharField(max_length=255, blank=True)
    billing_details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment {self.id} - {self.user.username} - {self.amount} {self.currency}"


class BillingAddress(models.Model):
    """
    User billing address information
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='billing_addresses')
    name = models.CharField(max_length=100)
    street_address = models.CharField(max_length=255)
    street_address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = CountryField()
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name}'s billing address in {self.city}, {self.country.name}"


class Invoice(models.Model):
    """
    Invoice model for storing billing history and receipts
    """
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('uncollectible', 'Uncollectible'),
        ('void', 'Void'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    stripe_invoice_id = models.CharField(max_length=100, blank=True)
    number = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    currency = models.CharField(max_length=3, default='USD')
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    invoice_pdf = models.URLField(blank=True)
    billing_address = models.ForeignKey(BillingAddress, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Invoice {self.number or self.id} - {self.user.username}" 
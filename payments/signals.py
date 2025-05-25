from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone

from .models import Subscription, Payment, Invoice

import stripe
import logging

logger = logging.getLogger(__name__)

# Initialize Stripe with the API key
stripe.api_key = settings.STRIPE_API_KEY


@receiver(post_save, sender=Subscription)
def subscription_created_or_updated(sender, instance, created, **kwargs):
    """
    Signal to handle subscription creation and updates
    """
    if created:
        # Log the creation of a new subscription
        logger.info(f"New subscription created for user {instance.user.username}")
        
        # If subscription was created, check if we need to create a Stripe subscription
        if not instance.stripe_subscription_id and instance.user.profile:
            try:
                # Create if there's no existing Stripe subscription ID
                if not instance.stripe_customer_id:
                    # Create a Stripe customer if one doesn't exist
                    customer = stripe.Customer.create(
                        email=instance.user.email,
                        name=f"{instance.user.first_name} {instance.user.last_name}".strip() or instance.user.username,
                        metadata={
                            'user_id': instance.user.id,
                        }
                    )
                    instance.stripe_customer_id = customer.id
                    instance.save(update_fields=['stripe_customer_id'])
                
                # Now create the subscription in Stripe
                stripe_subscription = stripe.Subscription.create(
                    customer=instance.stripe_customer_id,
                    items=[
                        {"price": instance.plan.stripe_price_id},
                    ],
                    metadata={
                        'subscription_id': instance.id,
                        'user_id': instance.user.id,
                    }
                )
                
                # Update our subscription with Stripe ID
                instance.stripe_subscription_id = stripe_subscription.id
                instance.status = stripe_subscription.status
                instance.save(update_fields=['stripe_subscription_id', 'status'])
                
            except stripe.error.StripeError as e:
                logger.error(f"Stripe error when creating subscription: {str(e)}")
    else:
        # Handle updates to the subscription
        if instance.stripe_subscription_id:
            try:
                # Update the subscription in Stripe if it already exists
                stripe_subscription = stripe.Subscription.retrieve(instance.stripe_subscription_id)
                
                # Handle subscription cancellation
                if instance.cancel_at_period_end and not stripe_subscription.cancel_at_period_end:
                    stripe.Subscription.modify(
                        instance.stripe_subscription_id,
                        cancel_at_period_end=True
                    )
                    logger.info(f"Subscription {instance.id} set to cancel at period end")
                
            except stripe.error.StripeError as e:
                logger.error(f"Stripe error when updating subscription: {str(e)}")


@receiver(post_save, sender=Payment)
def payment_created_or_updated(sender, instance, created, **kwargs):
    """
    Signal to handle payment creation and updates
    """
    if created and instance.status == 'completed' and instance.subscription:
        # Create an invoice for the payment
        Invoice.objects.create(
            user=instance.user,
            subscription=instance.subscription,
            payment=instance,
            status='paid',
            currency=instance.currency,
            amount_due=instance.amount,
            amount_paid=instance.amount,
            paid_at=timezone.now()
        )
        logger.info(f"Invoice created for payment {instance.id}") 
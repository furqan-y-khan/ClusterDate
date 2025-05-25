from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Plan, Subscription, Payment, PaymentMethod, BillingAddress, Invoice

import stripe
import json
import logging

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum
from django.db.models.functions import TruncDay, TruncMonth
from datetime import timedelta

logger = logging.getLogger(__name__)

# Initialize Stripe with the API key
stripe.api_key = settings.STRIPE_API_KEY


@login_required
def plan_list(request):
    """
    Display available subscription plans
    """
    active_plans = Plan.objects.filter(is_active=True).order_by('price')
    
    # Get user's current subscription if any
    try:
        current_subscription = Subscription.objects.get(
            user=request.user, 
            status='active',
            end_date__isnull=True
        )
    except Subscription.DoesNotExist:
        current_subscription = None
    
    context = {
        'plans': active_plans,
        'current_subscription': current_subscription,
    }
    return render(request, 'payments/plan_list.html', context)


@login_required
def subscribe(request, plan_id):
    """
    Handle subscription to a plan
    """
    plan = get_object_or_404(Plan, id=plan_id, is_active=True)
    
    # Check if user already has an active subscription
    try:
        current_subscription = Subscription.objects.get(
            user=request.user, 
            status='active',
            end_date__isnull=True
        )
        if current_subscription.plan.id == plan.id:
            messages.info(request, "You are already subscribed to this plan.")
            return redirect('payments:plan_list')
    except Subscription.DoesNotExist:
        current_subscription = None
    
    # Get default payment method if any
    try:
        default_payment_method = PaymentMethod.objects.get(
            user=request.user,
            is_default=True
        )
    except PaymentMethod.DoesNotExist:
        default_payment_method = None
    
    if request.method == 'POST':
        payment_method_id = request.POST.get('payment_method_id')
        
        if not payment_method_id:
            messages.error(request, "Please select a payment method.")
            return redirect('payments:subscribe', plan_id=plan.id)
        
        try:
            # Create or update subscription
            if current_subscription:
                # Upgrade/downgrade existing subscription
                stripe_subscription = stripe.Subscription.retrieve(
                    current_subscription.stripe_subscription_id
                )
                
                # Update the subscription items
                stripe.Subscription.modify(
                    current_subscription.stripe_subscription_id,
                    items=[{
                        'id': stripe_subscription['items']['data'][0].id,
                        'price': plan.stripe_price_id,
                    }],
                    payment_method=payment_method_id,
                )
                
                # Update our database
                current_subscription.plan = plan
                current_subscription.save()
                
                messages.success(request, f"Your subscription has been updated to {plan.name}.")
            else:
                # Create new subscription
                # First ensure user has a Stripe customer ID
                if not hasattr(request.user, 'stripe_customer'):
                    customer = stripe.Customer.create(
                        email=request.user.email,
                        name=f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                        payment_method=payment_method_id,
                        metadata={
                            'user_id': request.user.id,
                        }
                    )
                    stripe_customer_id = customer.id
                else:
                    stripe_customer_id = request.user.stripe_customer.id
                
                # Create the subscription
                stripe_subscription = stripe.Subscription.create(
                    customer=stripe_customer_id,
                    items=[
                        {"price": plan.stripe_price_id},
                    ],
                    payment_method=payment_method_id,
                    expand=['latest_invoice.payment_intent'],
                )
                
                # Create subscription in our database
                subscription = Subscription.objects.create(
                    user=request.user,
                    plan=plan,
                    status=stripe_subscription.status,
                    stripe_subscription_id=stripe_subscription.id,
                    stripe_customer_id=stripe_customer_id,
                )
                
                messages.success(request, f"You have successfully subscribed to {plan.name}!")
            
            return redirect('payments:plan_list')
            
        except stripe.error.CardError as e:
            error = e.error
            messages.error(request, f"Card error: {error.message}")
        except stripe.error.StripeError as e:
            messages.error(request, f"An error occurred while processing your payment. Please try again.")
            logger.error(f"Stripe error: {str(e)}")
    
    context = {
        'plan': plan,
        'default_payment_method': default_payment_method,
        'payment_methods': PaymentMethod.objects.filter(user=request.user),
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, 'payments/subscribe.html', context)


@login_required
def cancel_subscription(request):
    """
    Cancel current subscription
    """
    try:
        subscription = Subscription.objects.get(
            user=request.user, 
            status='active',
            end_date__isnull=True
        )
    except Subscription.DoesNotExist:
        messages.error(request, "You don't have an active subscription to cancel.")
        return redirect('payments:plan_list')
    
    if request.method == 'POST':
        try:
            # Cancel at period end in Stripe
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True
            )
            
            # Update our database
            subscription.cancel_at_period_end = True
            subscription.save()
            
            messages.success(request, "Your subscription has been canceled. "
                                     "You'll have access until the end of your billing period.")
            return redirect('payments:plan_list')
            
        except stripe.error.StripeError as e:
            messages.error(request, "An error occurred while canceling your subscription. "
                                  "Please try again or contact support.")
            logger.error(f"Stripe error when canceling subscription: {str(e)}")
    
    context = {
        'subscription': subscription,
    }
    return render(request, 'payments/cancel_subscription.html', context)


@login_required
def payment_method_list(request):
    """
    List all payment methods for the user
    """
    payment_methods = PaymentMethod.objects.filter(user=request.user)
    
    context = {
        'payment_methods': payment_methods,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, 'payments/payment_method_list.html', context)


@login_required
def add_payment_method(request):
    """
    Add a new payment method
    """
    if request.method == 'POST':
        payment_method_id = request.POST.get('payment_method_id')
        
        if not payment_method_id:
            messages.error(request, "Invalid payment information.")
            return redirect('payments:add_payment_method')
        
        try:
            # Retrieve the payment method details from Stripe
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
            
            # Check if this is the first payment method (make it default)
            is_default = not PaymentMethod.objects.filter(user=request.user).exists()
            
            # Save to our database
            card = payment_method.card
            PaymentMethod.objects.create(
                user=request.user,
                stripe_payment_method_id=payment_method_id,
                payment_type='card',
                last_4=card.last4,
                expiry_month=card.exp_month,
                expiry_year=card.exp_year,
                is_default=is_default
            )
            
            messages.success(request, "Payment method added successfully.")
            return redirect('payments:payment_method_list')
        
        except stripe.error.StripeError as e:
            messages.error(request, f"An error occurred: {str(e)}")
    
    context = {
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, 'payments/add_payment_method.html', context)


@login_required
def delete_payment_method(request, payment_method_id):
    """
    Delete a payment method
    """
    payment_method = get_object_or_404(PaymentMethod, stripe_payment_method_id=payment_method_id, user=request.user)
    
    if request.method == 'POST':
        # Check if it's the default and there are other payment methods
        if payment_method.is_default:
            other_methods = PaymentMethod.objects.filter(user=request.user).exclude(id=payment_method.id)
            if other_methods.exists():
                # Set another one as default
                new_default = other_methods.first()
                new_default.is_default = True
                new_default.save()
        
        # Delete from Stripe
        try:
            stripe.PaymentMethod.detach(payment_method_id)
        except stripe.error.StripeError as e:
            logger.error(f"Error detaching payment method from Stripe: {str(e)}")
        
        # Delete from our database
        payment_method.delete()
        messages.success(request, "Payment method deleted successfully.")
        return redirect('payments:payment_method_list')
    
    context = {
        'payment_method': payment_method,
    }
    return render(request, 'payments/delete_payment_method.html', context)


@login_required
def set_default_payment_method(request, payment_method_id):
    """
    Set a payment method as default
    """
    payment_method = get_object_or_404(PaymentMethod, stripe_payment_method_id=payment_method_id, user=request.user)
    
    if request.method == 'POST':
        # Remove default from all other payment methods
        PaymentMethod.objects.filter(user=request.user, is_default=True).update(is_default=False)
        
        # Set this one as default
        payment_method.is_default = True
        payment_method.save()
        
        messages.success(request, "Default payment method updated.")
        
    return redirect('payments:payment_method_list')


@login_required
def billing_address_list(request):
    """
    List all billing addresses for the user
    """
    addresses = BillingAddress.objects.filter(user=request.user)
    
    context = {
        'addresses': addresses,
    }
    return render(request, 'payments/billing_address_list.html', context)


@login_required
def add_billing_address(request):
    """
    Add a new billing address
    """
    if request.method == 'POST':
        # Create new address
        address = BillingAddress(
            user=request.user,
            name=request.POST.get('name'),
            street_address=request.POST.get('street_address'),
            street_address_line2=request.POST.get('street_address_line2', ''),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            postal_code=request.POST.get('postal_code'),
            country=request.POST.get('country'),
        )
        
        # Check if this should be the default address
        is_default = request.POST.get('is_default') == 'on'
        if is_default:
            # Remove default from all other addresses
            BillingAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
            address.is_default = True
        
        address.save()
        messages.success(request, "Billing address added successfully.")
        return redirect('payments:billing_address_list')
        
    context = {}
    return render(request, 'payments/add_billing_address.html', context)


@login_required
def edit_billing_address(request, address_id):
    """
    Edit a billing address
    """
    address = get_object_or_404(BillingAddress, id=address_id, user=request.user)
    
    if request.method == 'POST':
        # Update address
        address.name = request.POST.get('name')
        address.street_address = request.POST.get('street_address')
        address.street_address_line2 = request.POST.get('street_address_line2', '')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.postal_code = request.POST.get('postal_code')
        address.country = request.POST.get('country')
        
        # Check if this should be the default address
        is_default = request.POST.get('is_default') == 'on'
        if is_default and not address.is_default:
            # Remove default from all other addresses
            BillingAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
            address.is_default = True
        
        address.save()
        messages.success(request, "Billing address updated successfully.")
        return redirect('payments:billing_address_list')
        
    context = {
        'address': address,
    }
    return render(request, 'payments/edit_billing_address.html', context)


@login_required
def delete_billing_address(request, address_id):
    """
    Delete a billing address
    """
    address = get_object_or_404(BillingAddress, id=address_id, user=request.user)
    
    if request.method == 'POST':
        # Check if it's the default and there are other addresses
        if address.is_default:
            other_addresses = BillingAddress.objects.filter(user=request.user).exclude(id=address.id)
            if other_addresses.exists():
                # Set another one as default
                new_default = other_addresses.first()
                new_default.is_default = True
                new_default.save()
        
        # Delete address
        address.delete()
        messages.success(request, "Billing address deleted successfully.")
        return redirect('payments:billing_address_list')
    
    context = {
        'address': address,
    }
    return render(request, 'payments/delete_billing_address.html', context)


@login_required
def set_default_billing_address(request, address_id):
    """
    Set a billing address as default
    """
    address = get_object_or_404(BillingAddress, id=address_id, user=request.user)
    
    if request.method == 'POST':
        # Remove default from all other addresses
        BillingAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
        
        # Set this one as default
        address.is_default = True
        address.save()
        
        messages.success(request, "Default billing address updated.")
        
    return redirect('payments:billing_address_list')


@login_required
def invoice_list(request):
    """
    List all invoices for the user
    """
    invoices = Invoice.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'invoices': invoices,
    }
    return render(request, 'payments/invoice_list.html', context)


@login_required
def invoice_detail(request, invoice_id):
    """
    Show details of a specific invoice
    """
    invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)
    
    context = {
        'invoice': invoice,
    }
    return render(request, 'payments/invoice_detail.html', context)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Handle webhooks from Stripe
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        logger.error(f"Invalid Stripe webhook payload: {str(e)}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Invalid Stripe webhook signature: {str(e)}")
        return HttpResponse(status=400)
    
    # Handle the event
    if event.type == 'invoice.payment_succeeded':
        handle_payment_succeeded(event.data.object)
    elif event.type == 'invoice.payment_failed':
        handle_payment_failed(event.data.object)
    elif event.type == 'customer.subscription.deleted':
        handle_subscription_deleted(event.data.object)
    elif event.type == 'customer.subscription.updated':
        handle_subscription_updated(event.data.object)
    
    return HttpResponse(status=200)


def handle_payment_succeeded(invoice):
    """
    Handle successful payment webhook
    """
    # Find the subscription
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=invoice.subscription)
        
        # Create payment record
        payment = Payment.objects.create(
            user=subscription.user,
            subscription=subscription,
            amount=invoice.amount_paid / 100,  # Convert from cents
            currency=invoice.currency,
            stripe_payment_intent_id=invoice.payment_intent,
            status='completed',
            description=f"Payment for {subscription.plan.name} subscription",
        )
        
        # Create or update invoice
        Invoice.objects.create(
            user=subscription.user,
            subscription=subscription,
            payment=payment,
            stripe_invoice_id=invoice.id,
            number=invoice.number,
            status='paid',
            currency=invoice.currency,
            amount_due=invoice.amount_due / 100,
            amount_paid=invoice.amount_paid / 100,
            invoice_pdf=invoice.invoice_pdf,
            paid_at=timezone.now(),
        )
        
        logger.info(f"Payment succeeded for subscription {subscription.id}")
    except Subscription.DoesNotExist:
        logger.error(f"Subscription not found for invoice {invoice.id}")


def handle_payment_failed(invoice):
    """
    Handle failed payment webhook
    """
    # Find the subscription
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=invoice.subscription)
        
        # Create payment record
        Payment.objects.create(
            user=subscription.user,
            subscription=subscription,
            amount=invoice.amount_due / 100,  # Convert from cents
            currency=invoice.currency,
            stripe_payment_intent_id=invoice.payment_intent,
            status='failed',
            description=f"Failed payment for {subscription.plan.name} subscription",
        )
        
        # Update subscription status
        subscription.status = 'past_due'
        subscription.save()
        
        logger.info(f"Payment failed for subscription {subscription.id}")
    except Subscription.DoesNotExist:
        logger.error(f"Subscription not found for invoice {invoice.id}")


def handle_subscription_deleted(subscription_data):
    """
    Handle subscription deletion webhook
    """
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=subscription_data.id)
        subscription.status = subscription_data.status
        subscription.end_date = timezone.now()
        subscription.save()
        
        logger.info(f"Subscription {subscription.id} marked as ended")
    except Subscription.DoesNotExist:
        logger.error(f"Subscription not found for ID {subscription_data.id}")


def handle_subscription_updated(subscription_data):
    """
    Handle subscription update webhook
    """
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=subscription_data.id)
        subscription.status = subscription_data.status
        subscription.cancel_at_period_end = subscription_data.cancel_at_period_end
        
        # Update the subscription plan if it has changed
        if subscription_data.items.data:
            price_id = subscription_data.items.data[0].price.id
            try:
                plan = Plan.objects.get(stripe_price_id=price_id)
                subscription.plan = plan
            except Plan.DoesNotExist:
                logger.error(f"Plan not found for price ID {price_id}")
        
        subscription.save()
        logger.info(f"Subscription {subscription.id} updated")
    except Subscription.DoesNotExist:
        logger.error(f"Subscription not found for ID {subscription_data.id}")


# Admin Dashboard Views
@staff_member_required
def admin_dashboard(request):
    """
    Admin dashboard view with payment and subscription analytics
    """
    # Date ranges
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    start_of_month = today.replace(day=1)
    
    # Payment stats
    payments = Payment.objects.filter(status='completed')
    total_revenue = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    payments_this_month = payments.filter(created_at__date__gte=start_of_month)
    revenue_this_month = payments_this_month.aggregate(Sum('amount'))['amount__sum'] or 0
    payments_last_30d = payments.filter(created_at__date__gte=thirty_days_ago)
    
    # Subscription stats
    active_subscriptions = Subscription.objects.filter(status='active')
    active_count = active_subscriptions.count()
    canceled_count = Subscription.objects.filter(status='canceled').count()
    
    # Revenue by plan
    revenue_by_plan = payments.values('subscription__plan__name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Daily revenue trend for last 30 days
    daily_revenue = payments_last_30d.annotate(
        day=TruncDay('created_at')
    ).values('day').annotate(
        total=Sum('amount')
    ).order_by('day')
    
    # Format for chart
    dates = [(thirty_days_ago + timedelta(days=i)).isoformat() for i in range(31)]
    revenue_data = [0] * 31
    
    for item in daily_revenue:
        day_diff = (item['day'].date() - thirty_days_ago).days
        if 0 <= day_diff < 31:
            revenue_data[day_diff] = float(item['total'])
    
    chart_data = {
        'dates': dates,
        'revenue': revenue_data
    }
    
    # New subscribers trend
    new_subscribers = Subscription.objects.filter(
        created_at__date__gte=thirty_days_ago
    ).annotate(
        day=TruncDay('created_at')
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    subscriber_data = [0] * 31
    for item in new_subscribers:
        day_diff = (item['day'].date() - thirty_days_ago).days
        if 0 <= day_diff < 31:
            subscriber_data[day_diff] = item['count']
    
    subscriber_chart_data = {
        'dates': dates,
        'subscribers': subscriber_data
    }
    
    context = {
        'title': 'Payment Dashboard',
        'total_revenue': total_revenue,
        'revenue_this_month': revenue_this_month,
        'active_subscriptions': active_count,
        'canceled_subscriptions': canceled_count,
        'revenue_by_plan': revenue_by_plan,
        'chart_data': json.dumps(chart_data),
        'subscriber_chart_data': json.dumps(subscriber_chart_data),
    }
    
    return render(request, 'admin/payments/dashboard.html', context) 
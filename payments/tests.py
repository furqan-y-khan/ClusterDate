from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Plan, Subscription, Payment, PaymentMethod
import stripe
from unittest.mock import patch, MagicMock


class PlanModelTest(TestCase):
    """Tests for the Plan model"""
    
    def setUp(self):
        self.plan = Plan.objects.create(
            name="Premium",
            description="Premium plan with all features",
            price=19.99,
            interval="month",
            stripe_price_id="price_123456",
            features={"feature1": True, "feature2": True},
            is_active=True
        )
    
    def test_plan_creation(self):
        """Test that a plan is created correctly"""
        self.assertEqual(self.plan.name, "Premium")
        self.assertEqual(self.plan.price, 19.99)
        self.assertEqual(self.plan.interval, "month")
        self.assertTrue(self.plan.is_active)
        self.assertEqual(self.plan.features, {"feature1": True, "feature2": True})
    
    def test_plan_str_method(self):
        """Test the string representation of a plan"""
        self.assertEqual(str(self.plan), "Premium ($19.99/month)")


class SubscriptionModelTest(TestCase):
    """Tests for the Subscription model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        self.plan = Plan.objects.create(
            name="Premium",
            description="Premium plan with all features",
            price=19.99,
            interval="month",
            stripe_price_id="price_123456",
            is_active=True
        )
        
        self.subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='active',
            stripe_subscription_id='sub_123456',
            stripe_customer_id='cus_123456',
            start_date=timezone.now()
        )
    
    def test_subscription_creation(self):
        """Test that a subscription is created correctly"""
        self.assertEqual(self.subscription.user, self.user)
        self.assertEqual(self.subscription.plan, self.plan)
        self.assertEqual(self.subscription.status, 'active')
        self.assertEqual(self.subscription.stripe_subscription_id, 'sub_123456')
    
    def test_subscription_is_active(self):
        """Test the is_active property"""
        self.assertTrue(self.subscription.is_active)
        
        # Test with end date in the future
        future_date = timezone.now() + timezone.timedelta(days=10)
        self.subscription.end_date = future_date
        self.subscription.save()
        self.assertTrue(self.subscription.is_active)
        
        # Test with end date in the past
        past_date = timezone.now() - timezone.timedelta(days=10)
        self.subscription.end_date = past_date
        self.subscription.save()
        self.assertFalse(self.subscription.is_active)
        
        # Test with inactive status
        self.subscription.status = 'canceled'
        self.subscription.end_date = None
        self.subscription.save()
        self.assertFalse(self.subscription.is_active)
    
    def test_subscription_cancel(self):
        """Test the cancel method"""
        self.assertFalse(self.subscription.cancel_at_period_end)
        self.subscription.cancel()
        self.assertTrue(self.subscription.cancel_at_period_end)


class PaymentModelTest(TestCase):
    """Tests for the Payment model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        self.plan = Plan.objects.create(
            name="Premium",
            description="Premium plan with all features",
            price=19.99,
            interval="month",
            stripe_price_id="price_123456",
            is_active=True
        )
        
        self.subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='active',
            stripe_subscription_id='sub_123456',
            stripe_customer_id='cus_123456',
            start_date=timezone.now()
        )
        
        self.payment = Payment.objects.create(
            user=self.user,
            subscription=self.subscription,
            amount=19.99,
            currency='USD',
            stripe_payment_intent_id='pi_123456',
            status='completed',
            description='Payment for Premium subscription'
        )
    
    def test_payment_creation(self):
        """Test that a payment is created correctly"""
        self.assertEqual(self.payment.user, self.user)
        self.assertEqual(self.payment.subscription, self.subscription)
        self.assertEqual(self.payment.amount, 19.99)
        self.assertEqual(self.payment.currency, 'USD')
        self.assertEqual(self.payment.status, 'completed')
    
    def test_payment_str_method(self):
        """Test the string representation of a payment"""
        expected = f"Payment {self.payment.id} - testuser - 19.99 USD"
        self.assertEqual(str(self.payment), expected)


@patch('stripe.Subscription')
@patch('stripe.Customer')
class SubscriptionViewTest(TestCase):
    """Tests for the subscription related views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        self.plan = Plan.objects.create(
            name="Premium",
            description="Premium plan with all features",
            price=19.99,
            interval="month",
            stripe_price_id="price_123456",
            is_active=True
        )
        
        self.payment_method = PaymentMethod.objects.create(
            user=self.user,
            stripe_payment_method_id='pm_123456',
            payment_type='card',
            last_4='4242',
            expiry_month=12,
            expiry_year=2025,
            is_default=True
        )
    
    def test_plan_list_view(self, mock_customer, mock_subscription):
        """Test the plan list view"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('payments:plan_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payments/plan_list.html')
        self.assertIn('plans', response.context)
        self.assertIn(self.plan, response.context['plans'])
    
    def test_subscribe_view_get(self, mock_customer, mock_subscription):
        """Test the subscribe view GET request"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('payments:subscribe', args=[self.plan.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payments/subscribe.html')
        self.assertEqual(response.context['plan'], self.plan)
    
    @patch('stripe.PaymentMethod.retrieve')
    def test_subscribe_view_post(self, mock_payment_method, mock_customer, mock_subscription):
        """Test the subscribe view POST request"""
        # Mock stripe objects
        mock_customer.create.return_value = MagicMock(id='cus_mock')
        mock_subscription.create.return_value = MagicMock(
            id='sub_mock',
            status='active',
            items={'data': [MagicMock(id='si_mock')]},
            latest_invoice=MagicMock(payment_intent=MagicMock())
        )
        mock_payment_method.return_value = MagicMock(
            card=MagicMock(last4='4242', exp_month=12, exp_year=2025)
        )
        
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post(
            reverse('payments:subscribe', args=[self.plan.id]),
            {'payment_method_id': 'pm_123456'}
        )
        
        # Check that we redirect to plan list
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('payments:plan_list'))
        
        # Check that a subscription was created
        self.assertEqual(Subscription.objects.count(), 1)
        subscription = Subscription.objects.first()
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.plan, self.plan)
        self.assertEqual(subscription.status, 'active')
        
    def test_cancel_subscription_view(self, mock_customer, mock_subscription):
        """Test the cancel subscription view"""
        # Create a subscription for the user
        subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='active',
            stripe_subscription_id='sub_123456',
            stripe_customer_id='cus_123456',
            start_date=timezone.now()
        )
        
        mock_subscription.modify.return_value = MagicMock()
        
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('payments:cancel_subscription'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payments/cancel_subscription.html')
        
        # Submit cancellation
        response = self.client.post(reverse('payments:cancel_subscription'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('payments:plan_list'))
        
        # Check that the subscription is marked to cancel
        subscription.refresh_from_db()
        self.assertTrue(subscription.cancel_at_period_end)
        
        # Verify Stripe was called
        mock_subscription.modify.assert_called_once_with(
            subscription.stripe_subscription_id,
            cancel_at_period_end=True
        ) 
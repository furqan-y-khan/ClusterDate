from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import Plan, Subscription, Payment, PaymentMethod, BillingAddress, Invoice


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'interval', 'is_active', 'created_at')
    list_filter = ('is_active', 'interval')
    search_fields = ('name', 'description')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'start_date', 'end_date', 'is_active')
    list_filter = ('status', 'cancel_at_period_end')
    search_fields = ('user__username', 'user__email', 'stripe_subscription_id')
    date_hierarchy = 'created_at'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('status', 'currency')
    search_fields = ('user__username', 'user__email', 'stripe_payment_intent_id', 'description')
    date_hierarchy = 'created_at'


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'payment_type', 'last_4', 'is_default', 'created_at')
    list_filter = ('payment_type', 'is_default')
    search_fields = ('user__username', 'user__email', 'last_4')


@admin.register(BillingAddress)
class BillingAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'city', 'country', 'is_default')
    list_filter = ('country', 'is_default')
    search_fields = ('user__username', 'user__email', 'name', 'city', 'postal_code')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('user', 'number', 'amount_due', 'amount_paid', 'status', 'created_at')
    list_filter = ('status', 'currency')
    search_fields = ('user__username', 'user__email', 'number', 'stripe_invoice_id')
    date_hierarchy = 'created_at'


# Add an admin dashboard view for payment insights
class PaymentAdminSite(admin.AdminSite):
    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        
        # Add custom dashboard stats for payments app
        for app in app_list:
            if app['app_label'] == 'payments':
                # Get payment statistics
                total_payments = Payment.objects.filter(status='completed').count()
                total_revenue = Payment.objects.filter(status='completed').aggregate(
                    total=Sum('amount')
                )['total'] or 0
                active_subscriptions = Subscription.objects.filter(status='active').count()
                
                app['models'].append({
                    'name': 'Payment Dashboard',
                    'object_name': 'PaymentDashboard',
                    'admin_url': '/admin/payments/dashboard/',
                    'view_only': True,
                    'perms': {'view': True},
                    'statistics': {
                        'total_payments': total_payments,
                        'total_revenue': total_revenue,
                        'active_subscriptions': active_subscriptions,
                    }
                })
                break
        
        return app_list 
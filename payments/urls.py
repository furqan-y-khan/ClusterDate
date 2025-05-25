from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Subscription management
    path('plans/', views.plan_list, name='plan_list'),
    path('subscribe/<int:plan_id>/', views.subscribe, name='subscribe'),
    path('subscription/cancel/', views.cancel_subscription, name='cancel_subscription'),
    
    # Payment methods
    path('payment-methods/', views.payment_method_list, name='payment_method_list'),
    path('payment-methods/add/', views.add_payment_method, name='add_payment_method'),
    path('payment-methods/<str:payment_method_id>/delete/', views.delete_payment_method, name='delete_payment_method'),
    path('payment-methods/<str:payment_method_id>/set-default/', views.set_default_payment_method, name='set_default_payment_method'),
    
    # Billing addresses
    path('billing-address/', views.billing_address_list, name='billing_address_list'),
    path('billing-address/add/', views.add_billing_address, name='add_billing_address'),
    path('billing-address/<int:address_id>/edit/', views.edit_billing_address, name='edit_billing_address'),
    path('billing-address/<int:address_id>/delete/', views.delete_billing_address, name='delete_billing_address'),
    path('billing-address/<int:address_id>/set-default/', views.set_default_billing_address, name='set_default_billing_address'),
    
    # Invoices and payment history
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    
    # Stripe webhook
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    
    # Admin dashboard
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
] 
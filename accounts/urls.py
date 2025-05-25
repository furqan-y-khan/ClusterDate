from django.urls import path
from . import views
from core.views import profile_view

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_edit, name='profile_edit'),
    path('profile/<str:username>/', profile_view, name='profile_view'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('verify-identity/', views.verify_identity, name='verify_identity'),
    
    # Firebase Authentication
    path('firebase-login/', views.firebase_login_view, name='firebase_login'),
    path('firebase-register/', views.firebase_register_view, name='firebase_register'),
    path('firebase-auth/', views.firebase_auth, name='firebase_auth'),
    path('firebase-register-submit/', views.firebase_register, name='firebase_register'),
    
    # Notification settings
    path('update-fcm-token/', views.update_fcm_token, name='update_fcm_token'),
    
    # Account management
    path('delete-account/', views.delete_account, name='delete_account'),
    path('export-data/', views.export_user_data, name='export_user_data'),
    path('privacy-settings/', views.privacy_settings, name='privacy_settings'),
    
    # Onboarding wizard
    path('onboarding/', views.onboarding_start, name='onboarding_start'),
    path('onboarding/basics/', views.onboarding_basics, name='onboarding_basics'),
    path('onboarding/photos/', views.onboarding_photos, name='onboarding_photos'),
    path('onboarding/interests/', views.onboarding_interests, name='onboarding_interests'),
    path('onboarding/preferences/', views.onboarding_preferences, name='onboarding_preferences'),
    path('onboarding/complete/', views.onboarding_complete, name='onboarding_complete'),
] 
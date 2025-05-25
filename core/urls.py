from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('about/', views.about, name='about'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    
    # Match and Like endpoints
    path('like/<int:user_id>/', views.like_user, name='like_user'),
    path('unlike/<int:user_id>/', views.unlike_user, name='unlike_user'),
    path('matches/', views.user_matches, name='user_matches'),
    path('match-request/<int:user_id>/', views.send_match_request, name='send_match_request'),
    path('accept-match/<int:user_id>/', views.accept_match_request, name='accept_match_request'),
    path('decline-match/<int:user_id>/', views.decline_match_request, name='decline_match_request'),
    
    # Block and Report endpoints
    path('block/<int:user_id>/', views.block_user, name='block_user'),
    path('unblock/<int:user_id>/', views.unblock_user, name='unblock_user'),
    path('report/<int:user_id>/', views.report_user, name='report_user'),
    
    # Location endpoints
    path('update-location/', views.update_location, name='update_location'),
    path('nearby-users/', views.nearby_users, name='nearby_users'),
    
    # Add the error documentation URL pattern
    path('error-docs/', views.error_docs, name='error_docs'),
    
    # Add the test error URL pattern
    path('test-error/<str:error_type>/', views.test_error, name='test_error'),
] 
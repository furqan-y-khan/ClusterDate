from django.urls import path
from . import views

app_name = 'mainstream'

urlpatterns = [
    path('', views.index, name='mainstream_index'),
    path('profile/create/', views.create_profile, name='create_profile'),
    path('profile/view/', views.view_profile, name='view_profile'),
    path('browse/', views.browse_profiles, name='browse_profiles'),
    path('profile/<str:username>/', views.profile_detail, name='profile_detail'),
    path('profile/<str:username>/like/', views.like_profile, name='like_profile'),
    path('profile/<str:username>/unlike/', views.unlike_profile, name='unlike_profile'),
    path('matches/', views.matches, name='matches'),
    path('recommended/', views.recommended_profiles, name='recommended'),
] 
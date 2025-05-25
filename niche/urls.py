from django.urls import path
from . import views

app_name = 'niche'

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('browse/', views.browse, name='browse'),
    path('community/<str:community_slug>/', views.community, name='community'),
    path('all-communities/', views.all_communities, name='all_communities'),
    path('suggest/', views.suggest_community, name='suggest'),
] 
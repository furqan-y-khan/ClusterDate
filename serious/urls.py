from django.urls import path
from . import views

app_name = 'serious'

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('browse/', views.browse, name='browse'),
    path('verification/', views.verification, name='verification'),
    path('guidance/', views.guidance, name='guidance'),
    path('compatibility/', views.compatibility, name='compatibility'),
] 
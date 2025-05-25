from django.urls import path
from . import views

app_name = 'sugar'

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('browse/', views.browse, name='browse'),
    path('daddy-signup/', views.daddy_signup, name='daddy_signup'),
    path('baby-signup/', views.baby_signup, name='baby_signup'),
    path('safety/', views.safety, name='safety'),
    path('verification/', views.verification, name='verification'),
    path('premium/', views.premium, name='premium'),
]
from django.urls import path
from . import views

app_name = 'lgbtq'

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('browse/', views.browse, name='browse'),
    path('safety/', views.safety, name='safety'),
    path('events/', views.events, name='events'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
]
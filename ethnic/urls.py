from django.urls import path
from . import views

app_name = 'ethnic'

urlpatterns = [
    path('', views.index, name='ethnic_index'),
    path('browse/', views.browse, name='browse'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('compatibility/', views.compatibility, name='compatibility'),
    path('events/', views.events, name='events'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('community/<str:culture_code>/', views.community, name='community'),
] 
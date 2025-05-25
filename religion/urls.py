from django.urls import path
from . import views

app_name = 'religion'

urlpatterns = [
    path('', views.religion_home, name='index'),
    path('profile/', views.religion_profile, name='religion_profile'),
    path('get-denominations/', views.get_denominations, name='get_denominations'),
    path('matches/', views.religion_matches, name='religion_matches'),
    path('matches/<str:username>/', views.religion_match_detail, name='religion_match_detail'),
    path('about/', views.about, name='about'),
    path('communities/', views.communities, name='communities'),
    path('interfaith/', views.interfaith, name='interfaith'),
    path('community/<str:religion_code>/', views.community, name='community'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
] 
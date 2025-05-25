from django.urls import path
from . import views

app_name = 'casual'

urlpatterns = [
    path('', views.index, name='index'),
] 
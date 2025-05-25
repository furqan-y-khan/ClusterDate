from django.urls import path
from . import views

app_name = 'video_call'

urlpatterns = [
    path('initiate/<str:username>/', views.initiate_call, name='initiate_call'),
    path('room/<uuid:call_id>/', views.call_room, name='call_room'),
    path('end/<uuid:call_id>/', views.end_call, name='end_call'),
    path('accept/<uuid:call_id>/', views.accept_call, name='accept_call'),
    path('reject/<uuid:call_id>/', views.reject_call, name='reject_call'),
    path('history/', views.call_history, name='call_history'),
    path('feedback/<uuid:call_id>/', views.call_feedback, name='call_feedback'),
] 
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def index(request):
    """
    Main view for the casual dating app
    """
    return render(request, 'casual/index.html')

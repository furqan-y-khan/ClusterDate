from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login

def index(request):
    """
    Main view for the ethnic/cultural dating app
    """
    return render(request, 'ethnic/index.html')

@login_required
def browse(request):
    """
    Browse profiles for the ethnic/cultural dating app
    """
    return render(request, 'ethnic/browse.html', {
        'profiles': []  # Replace with actual profile data
    })

@login_required
def profile_edit(request):
    """
    Edit profile for the ethnic/cultural dating app
    """
    if request.method == 'POST':
        # Handle form submission (replace with actual form handling)
        messages.success(request, "Profile updated successfully!")
        return redirect('ethnic:ethnic_index')
    
    return render(request, 'ethnic/profile_edit.html')

def compatibility(request):
    """
    Cultural compatibility information page
    """
    return render(request, 'ethnic/compatibility.html')

def events(request):
    """
    Cultural events and gatherings page
    """
    return render(request, 'ethnic/events.html')

def how_it_works(request):
    """
    How the cultural dating app works page
    """
    return render(request, 'ethnic/how_it_works.html')

def register(request):
    """
    Registration view for ethnic/cultural dating
    """
    if request.user.is_authenticated:
        return redirect('ethnic:ethnic_index')
        
    if request.method == 'POST':
        # This would be handled by a form in a real app
        # For now, redirect to the main accounts registration
        return redirect('accounts:register')
    
    return render(request, 'ethnic/register.html')

def login_view(request):
    """
    Login view for ethnic/cultural dating
    """
    if request.user.is_authenticated:
        return redirect('ethnic:ethnic_index')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('ethnic:ethnic_index')
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'ethnic/login.html')

def community(request, culture_code):
    """
    View for a specific cultural community
    """
    # Convert culture code to human-readable name
    culture_names = {
        'hispanic': 'Hispanic/Latino',
        'asian': 'Asian',
        'african': 'African',
        'middle-eastern': 'Middle Eastern',
        'european': 'European',
        'caribbean': 'Caribbean',
        'indian': 'Indian',
        'other': 'Other'
    }
    
    culture_name = culture_names.get(culture_code, 'Unknown Culture')
    
    # In a real app, you'd query profiles that match this culture
    # For now, we're just passing the name to the template
    return render(request, 'ethnic/community.html', {
        'culture_code': culture_code,
        'culture_name': culture_name,
        'profiles': []  # This would be real profiles in production
    })

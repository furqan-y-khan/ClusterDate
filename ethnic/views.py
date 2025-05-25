from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import EthnicProfile # EthnicProfile should be imported
from .forms import EthnicProfileForm 

# Note: authenticate and login are imported locally in login_view where needed.

def index(request):
    """
    Main view for the ethnic/cultural dating app
    """
    context = {}
    if request.user.is_authenticated:
        try:
            # Check if EthnicProfile exists for the current user.
            # Accessing it is enough to trigger DoesNotExist if not found.
            _ = request.user.ethnic_profile 
            context['has_ethnic_profile'] = True
        except EthnicProfile.DoesNotExist:
            context['has_ethnic_profile'] = False
    else:
        # For unauthenticated users, they don't have a profile
        context['has_ethnic_profile'] = False 

    return render(request, 'ethnic/index.html', context)

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
    try:
        profile = request.user.ethnic_profile
    except EthnicProfile.DoesNotExist:
        profile = None

    if request.method == 'POST':
        form = EthnicProfileForm(request.POST, instance=profile)
        if form.is_valid():
            ethnic_profile_instance = form.save(commit=False)
            if profile is None: # Check if it's a new profile
                ethnic_profile_instance.user = request.user
            ethnic_profile_instance.save()
            form.save_m2m() # Important for saving ManyToMany fields

            messages.success(request, "Your ethnic profile has been updated successfully!")
            return redirect('ethnic:index') 
    else:
        form = EthnicProfileForm(instance=profile)

    return render(request, 'ethnic/profile_edit.html', {
        'form': form,
        'profile': profile
    })

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
        return redirect('ethnic:index')
        
    if request.method == 'POST':
        return redirect('accounts:register')
    
    return render(request, 'ethnic/register.html')

def login_view(request):
    """
    Login view for ethnic/cultural dating
    """
    from django.contrib.auth import authenticate, login # Moved import here
    if request.user.is_authenticated:
        return redirect('ethnic:index')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('ethnic:index')
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'ethnic/login.html')

def community(request, culture_code):
    """
    View for a specific cultural community
    """
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
    
    return render(request, 'ethnic/community.html', {
        'culture_code': culture_code,
        'culture_name': culture_name,
        'profiles': [] 
    })

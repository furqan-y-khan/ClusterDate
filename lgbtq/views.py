from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .models import LGBTQProfile
from .forms import LGBTQProfileForm, LGBTQRegistrationForm, LGBTQLoginForm

def index(request):
    """
    Main view for the LGBTQ+ dating app
    """
    return render(request, 'lgbtq/index.html')

def register(request):
    """
    Registration view for LGBTQ+ dating
    """
    if request.user.is_authenticated:
        return redirect('lgbtq:index')
        
    if request.method == 'POST':
        form = LGBTQRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Please complete your profile.")
            return redirect('lgbtq:profile_edit')
    else:
        form = LGBTQRegistrationForm()
    
    return render(request, 'lgbtq/register.html', {'form': form})

def login_view(request):
    """
    Login view for LGBTQ+ dating
    """
    if request.user.is_authenticated:
        return redirect('lgbtq:index')
        
    if request.method == 'POST':
        form = LGBTQLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('lgbtq:index')
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = LGBTQLoginForm()
    
    return render(request, 'lgbtq/login.html', {'form': form})

def logout_view(request):
    """
    Logout view for LGBTQ+ dating
    """
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('lgbtq:index')

@login_required
def profile_edit(request):
    """
    Edit LGBTQ+ profile
    """
    try:
        profile = request.user.lgbtq_profile
    except LGBTQProfile.DoesNotExist:
        profile = None
    
    if request.method == 'POST':
        form = LGBTQProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, "Your LGBTQ+ profile has been updated!")
            return redirect('lgbtq:index')
    else:
        form = LGBTQProfileForm(instance=profile)
    
    return render(request, 'lgbtq/profile_edit.html', {'form': form})

@login_required
def browse(request):
    """
    Browse LGBTQ+ profiles
    """
    try:
        user_profile = request.user.lgbtq_profile
    except LGBTQProfile.DoesNotExist:
        messages.warning(request, "Please complete your LGBTQ+ profile first.")
        return redirect('lgbtq:profile_edit')
    
    # Get all profiles except the current user's
    profiles = LGBTQProfile.objects.exclude(user=request.user)
    
    # Filter based on sexual orientation and gender identity preferences
    # This would be more complex in a real app
    
    return render(request, 'lgbtq/browse.html', {'profiles': profiles})

def safety(request):
    """
    Safety information page
    """
    return render(request, 'lgbtq/safety.html')

def events(request):
    """
    Community events page
    """
    return render(request, 'lgbtq/events.html')

def how_it_works(request):
    """
    How the app works page
    """
    return render(request, 'lgbtq/how_it_works.html')

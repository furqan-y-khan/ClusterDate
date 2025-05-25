from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .models import SeriousProfile
from .forms import SeriousProfileForm, SeriousRegistrationForm, SeriousLoginForm

def index(request):
    """
    Main view for the serious relationship dating app
    """
    return render(request, 'serious/index.html')

def register(request):
    """
    Registration view for serious dating
    """
    if request.user.is_authenticated:
        return redirect('serious:index')
        
    if request.method == 'POST':
        form = SeriousRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Please complete your profile.")
            return redirect('serious:profile_edit')
    else:
        form = SeriousRegistrationForm()
    
    return render(request, 'serious/register.html', {'form': form})

def login_view(request):
    """
    Login view for serious dating
    """
    if request.user.is_authenticated:
        return redirect('serious:index')
        
    if request.method == 'POST':
        form = SeriousLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('serious:index')
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = SeriousLoginForm()
    
    return render(request, 'serious/login.html', {'form': form})

def logout_view(request):
    """
    Logout view for serious dating
    """
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('serious:index')

@login_required
def profile_edit(request):
    """
    Edit serious dating profile
    """
    try:
        profile = request.user.serious_profile
    except SeriousProfile.DoesNotExist:
        profile = None
    
    if request.method == 'POST':
        form = SeriousProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, "Your relationship profile has been updated!")
            return redirect('serious:index')
    else:
        form = SeriousProfileForm(instance=profile)
    
    return render(request, 'serious/profile_edit.html', {'form': form})

@login_required
def browse(request):
    """
    Browse serious profiles
    """
    try:
        user_profile = request.user.serious_profile
    except SeriousProfile.DoesNotExist:
        messages.warning(request, "Please complete your relationship profile first.")
        return redirect('serious:profile_edit')
    
    # Get all profiles except the current user's
    profiles = SeriousProfile.objects.exclude(user=request.user)
    
    return render(request, 'serious/browse.html', {'profiles': profiles})

def verification(request):
    """
    Verification information page
    """
    return render(request, 'serious/verification.html')

def guidance(request):
    """
    Relationship guidance page
    """
    return render(request, 'serious/guidance.html')

def compatibility(request):
    """
    Compatibility matching explanation page
    """
    return render(request, 'serious/compatibility.html')

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .models import SugarProfile
from .forms import SugarProfileForm, SugarRegistrationForm, SugarLoginForm

def index(request):
    """
    Main view for the sugar dating app
    """
    return render(request, 'sugar/index.html')

def register(request):
    """
    General registration view for sugar dating
    """
    if request.user.is_authenticated:
        return redirect('sugar:index')
        
    if request.method == 'POST':
        form = SugarRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Please complete your profile.")
            return redirect('sugar:profile_edit')
    else:
        form = SugarRegistrationForm()
    
    return render(request, 'sugar/register.html', {'form': form})

def login_view(request):
    """
    Login view for sugar dating
    """
    if request.user.is_authenticated:
        return redirect('sugar:index')
        
    if request.method == 'POST':
        form = SugarLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('sugar:index')
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = SugarLoginForm()
    
    return render(request, 'sugar/login.html', {'form': form})

def logout_view(request):
    """
    Logout view for sugar dating
    """
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('sugar:index')

@login_required
def profile_edit(request):
    """
    Edit sugar profile
    """
    try:
        profile = request.user.sugar_profile
    except SugarProfile.DoesNotExist:
        profile = None
    
    if request.method == 'POST':
        form = SugarProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, "Your sugar profile has been updated!")
            return redirect('sugar:index')
    else:
        form = SugarProfileForm(instance=profile)
    
    return render(request, 'sugar/profile_edit.html', {'form': form})

@login_required
def browse(request):
    """
    Browse sugar profiles
    """
    try:
        user_profile = request.user.sugar_profile
    except SugarProfile.DoesNotExist:
        messages.warning(request, "Please complete your sugar profile first.")
        return redirect('sugar:profile_edit')
    
    # Filter profiles based on user type
    if user_profile.is_sugar_daddy or user_profile.is_sugar_mommy:
        profiles = SugarProfile.objects.filter(is_sugar_baby=True)
    else:
        profiles = SugarProfile.objects.filter(is_sugar_daddy=True) | SugarProfile.objects.filter(is_sugar_mommy=True)
    
    return render(request, 'sugar/browse.html', {'profiles': profiles})

def daddy_signup(request):
    """
    Specific registration for sugar daddies
    """
    if request.user.is_authenticated:
        return redirect('sugar:index')
        
    if request.method == 'POST':
        form = SugarRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create sugar profile
            SugarProfile.objects.create(user=user, is_sugar_daddy=True)
            login(request, user)
            messages.success(request, "Registration successful! Please complete your profile.")
            return redirect('sugar:profile_edit')
    else:
        form = SugarRegistrationForm()
    
    return render(request, 'sugar/daddy_signup.html', {'form': form})

def baby_signup(request):
    """
    Specific registration for sugar babies
    """
    if request.user.is_authenticated:
        return redirect('sugar:index')
        
    if request.method == 'POST':
        form = SugarRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create sugar profile
            SugarProfile.objects.create(user=user, is_sugar_baby=True)
            login(request, user)
            messages.success(request, "Registration successful! Please complete your profile.")
            return redirect('sugar:profile_edit')
    else:
        form = SugarRegistrationForm()
    
    return render(request, 'sugar/baby_signup.html', {'form': form})

def safety(request):
    """
    Safety information page
    """
    return render(request, 'sugar/safety.html')

def verification(request):
    """
    Verification information page
    """
    return render(request, 'sugar/verification.html')

def premium(request):
    """
    Premium features page
    """
    return render(request, 'sugar/premium.html')

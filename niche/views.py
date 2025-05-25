from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .models import NicheProfile, Community
from .forms import NicheProfileForm, NicheRegistrationForm, NicheLoginForm, CommunityForm

def index(request):
    """
    Main view for the niche/specialized dating app
    """
    return render(request, 'niche/index.html')

def register(request):
    """
    Registration view for niche dating
    """
    if request.user.is_authenticated:
        return redirect('niche:index')
        
    if request.method == 'POST':
        form = NicheRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Please complete your profile.")
            return redirect('niche:profile_edit')
    else:
        form = NicheRegistrationForm()
    
    return render(request, 'niche/register.html', {'form': form})

def login_view(request):
    """
    Login view for niche dating
    """
    if request.user.is_authenticated:
        return redirect('niche:index')
        
    if request.method == 'POST':
        form = NicheLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('niche:index')
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = NicheLoginForm()
    
    return render(request, 'niche/login.html', {'form': form})

def logout_view(request):
    """
    Logout view for niche dating
    """
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('niche:index')

@login_required
def profile_edit(request):
    """
    Edit niche dating profile
    """
    try:
        profile = request.user.niche_profile
    except NicheProfile.DoesNotExist:
        profile = None
    
    if request.method == 'POST':
        form = NicheProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            
            # Handle communities
            selected_communities = request.POST.getlist('communities')
            profile.communities.clear()
            for community_id in selected_communities:
                try:
                    community = Community.objects.get(id=community_id)
                    profile.communities.add(community)
                except Community.DoesNotExist:
                    pass
            
            messages.success(request, "Your niche dating profile has been updated!")
            return redirect('niche:index')
    else:
        form = NicheProfileForm(instance=profile)
    
    context = {
        'form': form,
        'communities': Community.objects.all(),
        'profile': profile,
    }
    
    return render(request, 'niche/profile_edit.html', context)

@login_required
def browse(request):
    """
    Browse niche profiles
    """
    try:
        user_profile = request.user.niche_profile
    except NicheProfile.DoesNotExist:
        messages.warning(request, "Please complete your niche dating profile first.")
        return redirect('niche:profile_edit')
    
    # Get community filtering
    community_slug = request.GET.get('community')
    if community_slug:
        try:
            community = Community.objects.get(slug=community_slug)
            profiles = NicheProfile.objects.filter(communities__in=[community]).exclude(user=request.user)
        except Community.DoesNotExist:
            profiles = NicheProfile.objects.exclude(user=request.user)
    else:
        profiles = NicheProfile.objects.exclude(user=request.user)
    
    context = {
        'profiles': profiles,
        'communities': Community.objects.all(),
        'selected_community': community_slug,
    }
    
    return render(request, 'niche/browse.html', context)

def community(request, community_slug):
    """
    View specific niche community
    """
    community = get_object_or_404(Community, slug=community_slug)
    profiles = NicheProfile.objects.filter(communities__in=[community])
    
    if request.user.is_authenticated:
        try:
            user_profile = request.user.niche_profile
            profiles = profiles.exclude(user=request.user)
        except NicheProfile.DoesNotExist:
            pass
    
    context = {
        'community': community,
        'profiles': profiles,
    }
    
    return render(request, 'niche/community.html', context)

def all_communities(request):
    """
    View all niche communities
    """
    communities = Community.objects.all().order_by('name')
    return render(request, 'niche/all_communities.html', {'communities': communities})

@login_required
def suggest_community(request):
    """
    Suggest a new niche community
    """
    if request.method == 'POST':
        form = CommunityForm(request.POST)
        if form.is_valid():
            community = form.save(commit=False)
            community.suggested_by = request.user
            community.is_approved = False
            community.save()
            messages.success(request, "Thank you for suggesting a new community! It will be reviewed by our team.")
            return redirect('niche:all_communities')
    else:
        form = CommunityForm()
    
    return render(request, 'niche/suggest_community.html', {'form': form})

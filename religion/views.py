from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Q, F, Case, When, FloatField, Value
from django.db.models.functions import Coalesce
from django.contrib.auth import authenticate, login

from .models import ReligionProfile
from .forms import ReligionProfileForm
from core.models import Match, Like


@login_required
def religion_home(request):
    """
    Home page for religion-based dating
    """
    try:
        # Check if user has a religion profile
        profile = request.user.religion_profile
        has_profile = True
    except (AttributeError, ReligionProfile.DoesNotExist):
        has_profile = False
    
    context = {
        'has_profile': has_profile,
    }
    
    return render(request, 'religion/home.html', context)


@login_required
def religion_profile(request):
    """
    Create or update religion profile
    """
    try:
        # Try to get existing profile
        profile = request.user.religion_profile
    except (AttributeError, ReligionProfile.DoesNotExist):
        # Create new profile if it doesn't exist
        profile = None
    
    if request.method == 'POST':
        form = ReligionProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            
            messages.success(request, "Your religion profile has been updated!")
            return redirect('religion:religion_home')
    else:
        form = ReligionProfileForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile,
        'denomination_choices': ReligionProfile.DENOMINATION_CHOICES,
    }
    
    return render(request, 'religion/profile_form.html', context)


@login_required
def get_denominations(request):
    """
    AJAX view to get denominations for a given religion
    """
    religion_code = request.GET.get('religion')
    if not religion_code:
        return JsonResponse({'choices': []})
    
    choices = ReligionProfile.DENOMINATION_CHOICES.get(religion_code, [])
    return JsonResponse({'choices': choices})


@login_required
def religion_matches(request):
    """
    Show religion-specific matches
    """
    try:
        # Make sure user has a religion profile
        user_profile = request.user.religion_profile
    except (AttributeError, ReligionProfile.DoesNotExist):
        messages.warning(request, "Please complete your religion profile first.")
        return redirect('religion:religion_profile')
    
    # Get all users with religion profiles, except the current user
    religion_profiles = ReligionProfile.objects.select_related('user')\
        .exclude(user=request.user)
    
    # Filter by religion preference if specified
    if user_profile.religion_preference:
        religion_profiles = religion_profiles.filter(religion=user_profile.religion_preference)
    
    # Filter by denomination preference if specified
    if user_profile.religion_preference and user_profile.denomination_preference:
        religion_profiles = religion_profiles.filter(denomination=user_profile.denomination_preference)
    
    # Filter by religiosity preferences
    religion_profiles = religion_profiles.filter(
        religiosity__gte=user_profile.min_religiosity_preference,
        religiosity__lte=user_profile.max_religiosity_preference
    )
    
    # If not interfaith willing, filter to same religion
    if not user_profile.interfaith_willingness:
        religion_profiles = religion_profiles.filter(religion=user_profile.religion)
    
    # Calculate compatibility scores and add to queryset
    matches = []
    for profile in religion_profiles:
        # Calculate compatibility score
        score = user_profile.compatibility_score(profile)
        
        # Only include matches with score > 0
        if score > 0:
            matches.append({
                'user': profile.user,
                'profile': profile,
                'compatibility': score,
                'compatibility_percent': int(score * 100),
            })
    
    # Sort by compatibility score (highest first)
    matches.sort(key=lambda x: x['compatibility'], reverse=True)
    
    context = {
        'matches': matches,
    }
    
    return render(request, 'religion/matches.html', context)


@login_required
def religion_match_detail(request, username):
    """
    Show detailed view of a religious match
    """
    match_user = get_object_or_404(User, username=username)
    try:
        match_profile = match_user.religion_profile
    except ReligionProfile.DoesNotExist:
        messages.error(request, "This user doesn't have a religion profile.")
        return redirect('religion:religion_matches')
    
    try:
        user_profile = request.user.religion_profile
        compatibility = user_profile.compatibility_score(match_profile)
        compatibility_percent = int(compatibility * 100)
    except ReligionProfile.DoesNotExist:
        compatibility = 0
        compatibility_percent = 0
    
    # Check if mutual match exists
    is_match = Match.objects.filter(
        (Q(user1=request.user) & Q(user2=match_user)) |
        (Q(user1=match_user) & Q(user2=request.user))
    ).exists()
    
    # Check if user has liked this profile
    has_liked = Like.objects.filter(
        from_user=request.user,
        to_user=match_user
    ).exists()
    
    context = {
        'match_user': match_user,
        'match_profile': match_profile,
        'compatibility': compatibility,
        'compatibility_percent': compatibility_percent,
        'is_match': is_match,
        'has_liked': has_liked,
    }
    
    return render(request, 'religion/match_detail.html', context)


def about(request):
    """
    About page for religion-based dating
    """
    return render(request, 'religion/about.html')


def communities(request):
    """
    Religious communities page
    """
    return render(request, 'religion/communities.html')


def interfaith(request):
    """
    Interfaith dating options page
    """
    return render(request, 'religion/interfaith.html')


def community(request, religion_code):
    """
    View for a specific religious community
    """
    # Convert religion code to human-readable name
    religion_names = {
        'CH': 'Christianity',
        'IS': 'Islam',
        'HI': 'Hinduism',
        'JU': 'Judaism',
        'BU': 'Buddhism',
        'SI': 'Sikhism',
        'OT': 'Other Faiths',
        'NO': 'Spiritual/Non-Religious'
    }
    
    religion_name = religion_names.get(religion_code, 'Unknown Faith')
    
    # In a real app, you'd query profiles that match this religion
    # For now, we're just passing the name to the template
    return render(request, 'religion/community.html', {
        'religion_code': religion_code,
        'religion_name': religion_name,
        'profiles': []  # This would be real profiles in production
    })


def register(request):
    """
    Registration view for religion-based dating
    """
    if request.user.is_authenticated:
        return redirect('religion:religion_home')
        
    if request.method == 'POST':
        # This would be handled by a form in a real app
        # For now, redirect to the main accounts registration
        return redirect('accounts:register')
    
    return render(request, 'religion/register.html')


def login_view(request):
    """
    Login view for religion-based dating
    """
    if request.user.is_authenticated:
        return redirect('religion:religion_home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('religion:religion_home')
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'religion/login.html')

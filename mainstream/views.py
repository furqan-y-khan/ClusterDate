from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q, Count, F, Case, When, IntegerField
from django.db import transaction
from django.middleware.csrf import get_token

from core.models import Profile, Match, Like, Block, Report, Interest
from core.utils import process_like_action, process_unlike_action
from .models import MainstreamProfile
from .forms import MainstreamProfileForm, MainstreamProfileSearchForm
from messaging.models import Conversation, Message

import random
import json
import logging

# Set up logger
logger = logging.getLogger(__name__)

def index(request):
    """
    Main view for the mainstream dating app
    """
    # Ensure CSRF token is set in cookie
    get_token(request)
    return render(request, 'mainstream/index.html')

@login_required
def create_profile(request):
    """
    Create or update a mainstream dating profile
    """
    core_profile = request.user.profile 
    
    # Check if user already has a mainstream profile
    try:
        mainstream_profile = core_profile.mainstream_profile
        form = MainstreamProfileForm(instance=mainstream_profile)
        is_new = False
    except MainstreamProfile.DoesNotExist:
        form = MainstreamProfileForm()
        is_new = True
    
    if request.method == 'POST':
        if is_new:
            form = MainstreamProfileForm(request.POST, request.FILES)
        else:
            form = MainstreamProfileForm(request.POST, request.FILES, instance=mainstream_profile)
            
        if form.is_valid():
            profile = form.save(commit=False)
            profile.profile = core_profile
            profile.save()
            
            messages.success(request, "Mainstream profile updated successfully!")
            return redirect('mainstream:view_profile')
    
    return render(request, 'mainstream/create_profile.html', {
        'form': form,
        'is_new': is_new
    })

@login_required
def view_profile(request):
    """
    View your own profile
    """
    try:
        mainstream_profile = request.user.profile.mainstream_profile
    except (Profile.DoesNotExist, MainstreamProfile.DoesNotExist):
        messages.info(request, "You need to create a mainstream profile first")
        return redirect('mainstream:create_profile')
        
    return render(request, 'mainstream/view_profile.html', {
        'profile': mainstream_profile
    })

@login_required
def browse_profiles(request):
    """
    Browse profiles with search and filtering options
    """
    try:
        user_profile = request.user.profile.mainstream_profile
    except (Profile.DoesNotExist, MainstreamProfile.DoesNotExist):
        messages.info(request, "You need to create a mainstream profile first")
        return redirect('mainstream:create_profile')
    
    form = MainstreamProfileSearchForm(request.GET)
    
    # Get blocked users to exclude
    blocked_users = Block.objects.filter(from_user=request.user).values_list('to_user', flat=True)
    users_who_blocked_me = Block.objects.filter(to_user=request.user).values_list('from_user', flat=True)
    excluded_users = list(blocked_users) + list(users_who_blocked_me) + [request.user.id]
    
    # Base queryset
    profiles = MainstreamProfile.objects.filter(
        profile__user__is_active=True
    ).exclude(
        profile__user__id__in=excluded_users
    ).select_related('profile', 'profile__user')
    
    # Apply search filters if form is valid
    if form.is_valid():
        data = form.cleaned_data
        
        if data.get('gender'):
            profiles = profiles.filter(profile__gender=data['gender'])
            
        if data.get('min_age') is not None:
            # This is a bit complex as we need to filter by calculated age
            profiles = profiles.filter(profile__birth_date__isnull=False)
            # We'd ideally use a database function here but for simplicity, 
            # we'll filter in Python after getting the data
            
        if data.get('max_age') is not None:
            profiles = profiles.filter(profile__birth_date__isnull=False)
            
        if data.get('relationship_status'):
            profiles = profiles.filter(relationship_status=data['relationship_status'])
            
        if data.get('looking_for'):
            profiles = profiles.filter(looking_for=data['looking_for'])
            
        if data.get('education_level'):
            profiles = profiles.filter(education_level=data['education_level'])
            
        if data.get('distance') and request.user.profile.latitude and request.user.profile.longitude:
            # This would ideally use a spatial query, but for now we'll filter later
            profiles = profiles.filter(profile__latitude__isnull=False, profile__longitude__isnull=False)
    
    # Post database query filtering for complex criteria
    filtered_profiles = []
    for profile in profiles:
        # Skip profiles that don't meet age criteria if specified
        if form.is_valid():
            data = form.cleaned_data
            if data.get('min_age') is not None and profile.profile.age and profile.profile.age < data['min_age']:
                continue
            if data.get('max_age') is not None and profile.profile.age and profile.profile.age > data['max_age']:
                continue
                
            # Distance filtering
            if data.get('distance') and request.user.profile.latitude and request.user.profile.longitude:
                distance = request.user.profile.distance_to(profile.profile)
                if distance is None or distance > data['distance']:
                    continue
        
        # Calculate match score
        match_score = user_profile.get_match_score(profile)
        profile.match_score = match_score
        filtered_profiles.append(profile)
    
    # Sort by match score (highest first)
    filtered_profiles.sort(key=lambda x: x.match_score, reverse=True)
    
    # Pagination
    paginator = Paginator(filtered_profiles, 10)  # 10 profiles per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Check which profiles the user has already liked
    user_likes = Like.objects.filter(
        from_user=request.user
    ).values_list('to_user_id', flat=True)
    
    # Add like status to each profile
    for profile in page_obj:
        profile.is_liked = profile.profile.user.id in user_likes
    
    return render(request, 'mainstream/browse_profiles.html', {
        'form': form,
        'page_obj': page_obj,
    })

@login_required
def profile_detail(request, username):
    """
    View another user's profile
    """
    user = get_object_or_404(Profile, user__username=username).user
    
    # Check if blocked
    if Block.objects.filter(Q(from_user=request.user, to_user=user) | 
                            Q(from_user=user, to_user=request.user)).exists():
        messages.error(request, "You cannot view this profile")
        return redirect('mainstream:browse_profiles')
    
    mainstream_profile = get_object_or_404(MainstreamProfile, profile__user=user)
    
    # Check if user has liked this profile
    is_liked = Like.objects.filter(from_user=request.user, to_user=user).exists()
    
    # Check if there's a match
    is_matched = Match.objects.filter(
        (Q(user1=request.user, user2=user) | Q(user1=user, user2=request.user))
    ).exists()
    
    # Check if we have a conversation
    conversation = None
    if is_matched:
        conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=user
        ).first()
    
    # Calculate match score
    try:
        user_profile = request.user.profile.mainstream_profile
        match_score = user_profile.get_match_score(mainstream_profile)
    except (Profile.DoesNotExist, MainstreamProfile.DoesNotExist):
        match_score = 0
    
    return render(request, 'mainstream/profile_detail.html', {
        'profile': mainstream_profile,
        'is_liked': is_liked,
        'is_matched': is_matched,
        'match_score': match_score,
        'conversation': conversation
    })

@login_required
@require_POST
def like_profile(request, username):
    """
    Like a profile and check for a match
    """
    return process_like_action(request, username)

@login_required
@require_POST
def unlike_profile(request, username):
    """
    Unlike a profile
    """
    return process_unlike_action(request, username)

@login_required
def matches(request):
    """
    View all matches
    """
    # Get all matches
    matches = Match.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).select_related('user1', 'user2')
    
    # Format matches for display
    formatted_matches = []
    for match in matches:
        other_user = match.user2 if match.user1 == request.user else match.user1
        
        try:
            # Get the other user's profile
            other_profile = other_user.profile
            other_mainstream_profile = other_profile.mainstream_profile
            
            # Check if we have a conversation
            conversation = Conversation.objects.filter(
                participants=request.user
            ).filter(
                participants=other_user
            ).first()
            
            # Check if there are unread messages
            unread_count = 0
            if conversation:
                unread_count = Message.objects.filter(
                    conversation=conversation,
                    sender=other_user,
                    is_read=False
                ).count()
            
            formatted_matches.append({
                'match': match,
                'other_user': other_user,
                'profile': other_profile,
                'mainstream_profile': other_mainstream_profile,
                'conversation': conversation,
                'unread_count': unread_count
            })
        except (Profile.DoesNotExist, MainstreamProfile.DoesNotExist):
            # Skip matches with incomplete profiles
            continue
    
    return render(request, 'mainstream/matches.html', {
        'matches': formatted_matches
    })

@login_required
def recommended_profiles(request):
    """
    Get profiles recommended based on the matching algorithm
    """
    try:
        user_profile = request.user.profile.mainstream_profile
    except (Profile.DoesNotExist, MainstreamProfile.DoesNotExist):
        messages.info(request, "You need to create a mainstream profile first")
        return redirect('mainstream:create_profile')
    
    # Get blocked users to exclude
    blocked_users = Block.objects.filter(from_user=request.user).values_list('to_user', flat=True)
    users_who_blocked_me = Block.objects.filter(to_user=request.user).values_list('from_user', flat=True)
    excluded_users = list(blocked_users) + list(users_who_blocked_me) + [request.user.id]
    
    # Get already liked users
    liked_users = Like.objects.filter(from_user=request.user).values_list('to_user', flat=True)
    
    # Get mainstream profiles to consider
    profiles = MainstreamProfile.objects.filter(
        profile__user__is_active=True
    ).exclude(
        profile__user__id__in=excluded_users + list(liked_users)
    ).select_related('profile', 'profile__user')
    
    # Calculate match scores
    scored_profiles = []
    for profile in profiles:
        match_score = user_profile.get_match_score(profile)
        profile.match_score = match_score
        scored_profiles.append(profile)
    
    # Sort by match score (highest first)
    scored_profiles.sort(key=lambda x: x.match_score, reverse=True)
    
    # Take top 10 recommended profiles
    recommended = scored_profiles[:10]
    
    return render(request, 'mainstream/recommended.html', {
        'profiles': recommended
    })

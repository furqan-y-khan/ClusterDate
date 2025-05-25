from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from .models import Profile, Match, Like, Block, Report, Interest, MatchRequest, Notification
from django.db import models
import json
from django.conf import settings
import googlemaps
from .matching import get_matches_for_user, get_machine_learning_recommendations

# Initialize Google Maps client
try:
    gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
except ValueError:
    # Use a dummy client for development if API key is invalid
    gmaps = None

def home(request):
    """
    Home page view that displays all dating categories
    """
    return render(request, 'core/home.html')

def about(request):
    """
    About page view
    """
    return render(request, 'core/about.html')

def privacy_policy(request):
    """
    Privacy policy page view
    """
    return render(request, 'core/privacy_policy.html')

def terms_of_service(request):
    """
    Terms of service page view
    """
    return render(request, 'core/terms_of_service.html')

@login_required
def profile_view(request, username):
    """
    View to display a user's profile
    """
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)
    
    # Check if the current user has blocked or been blocked by the profile user
    is_blocked = Block.objects.filter(from_user=request.user, to_user=user).exists()
    is_blocked_by = Block.objects.filter(from_user=user, to_user=request.user).exists()
    
    if is_blocked_by:
        messages.error(request, "You cannot view this profile as you have been blocked by the user.")
        return redirect('home')
    
    # Check if the current user has liked the profile user
    has_liked = Like.objects.filter(from_user=request.user, to_user=user).exists()
    
    # Check if there's a mutual match - both users have liked each other
    user_likes_other = Like.objects.filter(from_user=request.user, to_user=user).exists()
    other_likes_user = Like.objects.filter(from_user=user, to_user=request.user).exists()
    is_match = user_likes_other and other_likes_user
    
    context = {
        'profile_user': user,
        'profile': profile,
        'is_blocked': is_blocked,
        'has_liked': has_liked,
        'is_match': is_match,
    }
    
    return render(request, 'accounts/profile_view.html', context)

@login_required
@require_POST
def like_profile(request, username):
    """
    View to like a user's profile
    """
    user = get_object_or_404(User, username=username)
    
    # Check if the user is trying to like themselves
    if user == request.user:
        return JsonResponse({'status': 'error', 'message': 'You cannot like your own profile.'})
    
    # Check if the user has already liked this profile
    if Like.objects.filter(from_user=request.user, to_user=user).exists():
        return JsonResponse({'status': 'error', 'message': 'You have already liked this profile.'})
    
    # Create the like
    like = Like.objects.create(from_user=request.user, to_user=user)
    
    # Check if there's a mutual like
    mutual_like = Like.objects.filter(from_user=user, to_user=request.user).exists()
    
    if mutual_like:
        # Create a match
        match, created = Match.objects.get_or_create(
            user1=request.user,
            user2=user,
            defaults={'is_mutual': True}
        )
        
        if not created:
            match.is_mutual = True
            match.save()
        
        return JsonResponse({
            'status': 'success', 
            'message': 'It\'s a match! You can now message each other.',
            'is_match': True
        })
    
    return JsonResponse({
        'status': 'success', 
        'message': 'Profile liked successfully.',
        'is_match': False
    })

@login_required
@require_POST
def block_profile(request, username):
    """
    View to block a user's profile
    """
    user = get_object_or_404(User, username=username)
    
    # Check if the user is trying to block themselves
    if user == request.user:
        return JsonResponse({'status': 'error', 'message': 'You cannot block your own profile.'})
    
    # Check if the user has already blocked this profile
    if Block.objects.filter(from_user=request.user, to_user=user).exists():
        return JsonResponse({'status': 'error', 'message': 'You have already blocked this profile.'})
    
    # Create the block
    reason = request.POST.get('reason', '')
    block = Block.objects.create(from_user=request.user, to_user=user, reason=reason)
    
    # Remove any likes or matches
    Like.objects.filter(from_user=request.user, to_user=user).delete()
    Like.objects.filter(from_user=user, to_user=request.user).delete()
    Match.objects.filter(
        (models.Q(user1=request.user) & models.Q(user2=user)) | 
        (models.Q(user1=user) & models.Q(user2=request.user))
    ).delete()
    
    return JsonResponse({
        'status': 'success', 
        'message': 'Profile blocked successfully.'
    })

@login_required
@require_POST
def report_profile(request, username):
    """
    View to report a user's profile
    """
    user = get_object_or_404(User, username=username)
    
    # Check if the user is trying to report themselves
    if user == request.user:
        return JsonResponse({'status': 'error', 'message': 'You cannot report your own profile.'})
    
    # Get report details
    report_type = request.POST.get('report_type')
    details = request.POST.get('details', '')
    
    # Create the report
    report = Report.objects.create(
        from_user=request.user,
        against_user=user,
        report_type=report_type,
        details=details
    )
    
    return JsonResponse({
        'status': 'success', 
        'message': 'Profile reported successfully. Our team will review your report.'
    })

@login_required
@require_POST
def update_location(request):
    """
    Update user's location using coordinates
    """
    try:
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not latitude or not longitude:
            return JsonResponse({'success': False, 'error': 'Latitude and longitude are required'}, status=400)
        
        # Get geocoding information
        location_name = ""
        if gmaps:
            try:
                reverse_geocode_result = gmaps.reverse_geocode((latitude, longitude))
                
                # Extract location name if available
                if reverse_geocode_result and len(reverse_geocode_result) > 0:
                    # Try to get a meaningful location name (city, neighborhood, etc.)
                    for component in reverse_geocode_result[0]['address_components']:
                        if 'locality' in component['types']:
                            location_name = component['long_name']
                            break
                    
                    # If no locality found, use a broader area name
                    if not location_name:
                        for component in reverse_geocode_result[0]['address_components']:
                            if 'administrative_area_level_1' in component['types']:
                                location_name = component['long_name']
                                break
                    
                    # If still no name found, use the formatted address
                    if not location_name and 'formatted_address' in reverse_geocode_result[0]:
                        location_name = reverse_geocode_result[0]['formatted_address']
            except Exception as e:
                # If geocoding fails, just use coordinates as location
                location_name = f"Location at {latitude:.4f}, {longitude:.4f}"
        else:
            # If gmaps client is not available, use coordinates as location
            location_name = f"Location at {latitude:.4f}, {longitude:.4f}"
        
        # Update user's profile
        profile = request.user.profile
        profile.update_location(latitude, longitude)
        
        # Update location name if found
        if location_name:
            profile.location = location_name
            profile.save()
        
        return JsonResponse({
            'success': True,
            'location': profile.location,
            'latitude': profile.latitude,
            'longitude': profile.longitude
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def nearby_users(request):
    """
    Find users near the current user
    """
    try:
        # Get parameters with defaults
        max_distance = int(request.GET.get('max_distance', request.user.profile.distance_preference))
        min_age = int(request.GET.get('min_age', request.user.profile.min_age_preference))
        max_age = int(request.GET.get('max_age', request.user.profile.max_age_preference))
        gender = request.GET.get('gender', None)
        
        # Get current user's profile
        profile = request.user.profile
        
        if not profile.latitude or not profile.longitude:
            return JsonResponse({'success': False, 'error': 'Your location is not set'}, status=400)
        
        # Get all profiles
        all_profiles = Profile.objects.exclude(user=request.user).select_related('user')
        
        # Filter by location and other criteria
        nearby_profiles = []
        for other_profile in all_profiles:
            # Skip profiles without location
            if not other_profile.latitude or not other_profile.longitude:
                continue
            
            # Calculate distance
            distance = profile.distance_to(other_profile)
            
            # Skip if too far
            if distance is None or distance > max_distance:
                continue
            
            # Filter by age
            age = other_profile.age
            if age is None or age < min_age or age > max_age:
                continue
            
            # Filter by gender if specified
            if gender and other_profile.gender != gender:
                continue
            
            # Check if already matched or liked
            is_matched = Match.objects.filter(
                (models.Q(user1=request.user) & models.Q(user2=other_profile.user)) |
                (models.Q(user1=other_profile.user) & models.Q(user2=request.user)),
                is_mutual=True
            ).exists()
            
            has_liked = Like.objects.filter(
                from_user=request.user,
                to_user=other_profile.user
            ).exists()
            
            # Add to result with distance
            nearby_profiles.append({
                'user_id': other_profile.user.id,
                'username': other_profile.user.username,
                'profile_pic': other_profile.profile_picture.url if other_profile.profile_picture else None,
                'age': age,
                'gender': other_profile.get_gender_display(),
                'location': other_profile.location,
                'distance': round(distance, 1),
                'is_matched': is_matched,
                'has_liked': has_liked
            })
        
        # Sort by distance
        nearby_profiles.sort(key=lambda x: x['distance'])
        
        return JsonResponse({
            'success': True,
            'nearby_users': nearby_profiles
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def match_view(request):
    """
    View to display potential matches for the user
    """
    user = request.user
    
    # Get potential matches using advanced algorithm
    potential_matches = get_matches_for_user(user, limit=20)
    
    # Get ML-based recommendations if available
    try:
        ml_recommendations = get_machine_learning_recommendations(user, limit=5)
    except Exception as e:
        ml_recommendations = []
    
    # Combine regular matches with ML recommendations
    ml_user_ids = [u.id for u in ml_recommendations]
    
    # Add ML recommendations that aren't already in potential_matches
    for ml_user in ml_recommendations:
        if not any(match[0].id == ml_user.id for match in potential_matches):
            # Use a default score for ML recommendations
            potential_matches.append((ml_user, 0.75))
    
    # Sort by score
    potential_matches.sort(key=lambda x: x[1], reverse=True)
    
    # Format for template
    formatted_matches = []
    for match_user, score in potential_matches:
        # Calculate match percentage for display
        match_percentage = int(score * 100)
        
        formatted_matches.append({
            'user': match_user,
            'profile': match_user.profile,
            'match_percentage': match_percentage,
            'common_interests': set(user.profile.interests.all()) & set(match_user.profile.interests.all()),
        })
    
    context = {
        'matches': formatted_matches,
    }
    
    return render(request, 'core/match.html', context)

@login_required
@require_POST
def like_user(request, user_id):
    """
    View to like a user by ID
    """
    user = get_object_or_404(User, id=user_id)
    
    # Check if the user is trying to like themselves
    if user == request.user:
        return JsonResponse({'status': 'error', 'message': 'You cannot like your own profile.'})
    
    # Check if the user has already liked this profile
    if Like.objects.filter(from_user=request.user, to_user=user).exists():
        return JsonResponse({'status': 'error', 'message': 'You have already liked this profile.'})
    
    # Create the like
    like = Like.objects.create(from_user=request.user, to_user=user)
    
    # Check if there's a mutual like
    mutual_like = Like.objects.filter(from_user=user, to_user=request.user).exists()
    
    if mutual_like:
        # Create a match
        match, created = Match.objects.get_or_create(
            user1=request.user,
            user2=user,
            defaults={'is_mutual': True}
        )
        
        if not created:
            match.is_mutual = True
            match.save()
        
        return JsonResponse({
            'status': 'success', 
            'message': 'It\'s a match! You can now message each other.',
            'is_match': True
        })
    
    return JsonResponse({
        'status': 'success', 
        'message': 'Profile liked successfully.',
        'is_match': False
    })

@login_required
@require_POST
def unlike_user(request, user_id):
    """
    View to unlike a user by ID
    """
    user = get_object_or_404(User, id=user_id)
    
    # Check if the user has liked this profile
    like = Like.objects.filter(from_user=request.user, to_user=user).first()
    
    if not like:
        return JsonResponse({'status': 'error', 'message': 'You have not liked this profile.'})
    
    # Delete the like
    like.delete()
    
    # Check if there's a match and update it
    match = Match.objects.filter(
        (models.Q(user1=request.user) & models.Q(user2=user)) | 
        (models.Q(user1=user) & models.Q(user2=request.user))
    ).first()
    
    if match:
        match.is_mutual = False
        match.save()
    
    return JsonResponse({
        'status': 'success', 
        'message': 'Profile unliked successfully.'
    })

@login_required
def user_matches(request):
    """
    View to display user's matches and pending match requests
    """
    # Get pending match requests (matches initiated by others, waiting for user's approval)
    pending_matches = []
    pending_match_requests = MatchRequest.objects.filter(to_user=request.user, status='PENDING')
    for match_req in pending_match_requests:
        pending_matches.append(match_req.from_user)
    
    # Get connected matches (mutual matches)
    connected_matches = []
    matches = Match.objects.filter(
        (models.Q(user1=request.user) | models.Q(user2=request.user))
    )
    
    for match in matches:
        if match.user1 == request.user:
            connected_matches.append(match.user2)
        else:
            connected_matches.append(match.user1)
    
    context = {
        'pending_matches': pending_matches,
        'connected_matches': connected_matches
    }
    
    return render(request, 'core/matches.html', context)

@login_required
@require_POST
def send_match_request(request, user_id):
    """
    Send a match request to another user
    """
    to_user = get_object_or_404(User, id=user_id)
    
    # Check if the user is trying to match with themselves
    if to_user == request.user:
        return JsonResponse({'status': 'error', 'message': 'You cannot match with yourself.'})
    
    # Check if a match request already exists
    if MatchRequest.objects.filter(from_user=request.user, to_user=to_user).exists():
        return JsonResponse({'status': 'error', 'message': 'You have already sent a match request to this user.'})
    
    # Create the match request
    match_request = MatchRequest.objects.create(
        from_user=request.user, 
        to_user=to_user,
        status='PENDING'
    )
    
    # Check if the other user has already sent a match request
    existing_request = MatchRequest.objects.filter(from_user=to_user, to_user=request.user).first()
    
    if existing_request:
        # It's a mutual match!
        existing_request.status = 'ACCEPTED'
        existing_request.save()
        
        match_request.status = 'ACCEPTED'
        match_request.save()
        
        # Create a match in the Match model
        match = Match.objects.create(user1=request.user, user2=to_user)
        
        # Create notifications for both users
        Notification.objects.create(
            user=request.user,
            notification_type='MATCH',
            content=f"You matched with {to_user.username}!",
            related_user=to_user
        )
        
        Notification.objects.create(
            user=to_user,
            notification_type='MATCH',
            content=f"You matched with {request.user.username}!",
            related_user=request.user
        )
        
        return JsonResponse({
            'status': 'match', 
            'message': f"It's a match! You and {to_user.username} can now message each other."
        })
    
    # Create a notification for the recipient
    Notification.objects.create(
        user=to_user,
        notification_type='MATCH_REQUEST',
        content=f"{request.user.username} wants to match with you!",
        related_user=request.user
    )
    
    return JsonResponse({
        'status': 'success', 
        'message': f"Match request sent to {to_user.username}."
    })

@login_required
@require_POST
def accept_match_request(request, user_id):
    """
    Accept a match request from another user
    """
    from_user = get_object_or_404(User, id=user_id)
    
    # Check if there's a pending match request
    match_request = get_object_or_404(
        MatchRequest, 
        from_user=from_user, 
        to_user=request.user,
        status='PENDING'
    )
    
    # Accept the match request
    match_request.status = 'ACCEPTED'
    match_request.save()
    
    # Create a match in the Match model
    match = Match.objects.create(user1=from_user, user2=request.user)
    
    # Create notifications for both users
    Notification.objects.create(
        user=request.user,
        notification_type='MATCH',
        content=f"You matched with {from_user.username}!",
        related_user=from_user
    )
    
    Notification.objects.create(
        user=from_user,
        notification_type='MATCH',
        content=f"You matched with {request.user.username}!",
        related_user=request.user
    )
    
    return JsonResponse({
        'status': 'success', 
        'message': f"You've matched with {from_user.username}!"
    })

@login_required
@require_POST
def decline_match_request(request, user_id):
    """
    Decline a match request from another user
    """
    from_user = get_object_or_404(User, id=user_id)
    
    # Check if there's a pending match request
    match_request = get_object_or_404(
        MatchRequest, 
        from_user=from_user, 
        to_user=request.user,
        status='PENDING'
    )
    
    # Decline the match request
    match_request.status = 'DECLINED'
    match_request.save()
    
    return JsonResponse({
        'status': 'success', 
        'message': f"Match request from {from_user.username} declined."
    })

@login_required
@require_POST
def block_user(request, user_id):
    """
    View to block a user by ID
    """
    user = get_object_or_404(User, id=user_id)
    
    # Check if the user is trying to block themselves
    if user == request.user:
        return JsonResponse({'status': 'error', 'message': 'You cannot block your own profile.'})
    
    # Check if the user has already blocked this profile
    if Block.objects.filter(from_user=request.user, to_user=user).exists():
        return JsonResponse({'status': 'error', 'message': 'You have already blocked this profile.'})
    
    # Create the block
    reason = request.POST.get('reason', '')
    block = Block.objects.create(from_user=request.user, to_user=user, reason=reason)
    
    # Remove any likes or matches
    Like.objects.filter(from_user=request.user, to_user=user).delete()
    Like.objects.filter(from_user=user, to_user=request.user).delete()
    Match.objects.filter(
        (models.Q(user1=request.user) & models.Q(user2=user)) | 
        (models.Q(user1=user) & models.Q(user2=request.user))
    ).delete()
    
    return JsonResponse({
        'status': 'success', 
        'message': 'Profile blocked successfully.'
    })

@login_required
@require_POST
def unblock_user(request, user_id):
    """
    View to unblock a user by ID
    """
    user = get_object_or_404(User, id=user_id)
    
    # Check if the user has blocked this profile
    block = Block.objects.filter(from_user=request.user, to_user=user).first()
    
    if not block:
        return JsonResponse({'status': 'error', 'message': 'You have not blocked this profile.'})
    
    # Delete the block
    block.delete()
    
    return JsonResponse({
        'status': 'success', 
        'message': 'Profile unblocked successfully.'
    })

@login_required
@require_POST
def report_user(request, user_id):
    """
    View to report a user by ID
    """
    user = get_object_or_404(User, id=user_id)
    
    # Check if the user is trying to report themselves
    if user == request.user:
        return JsonResponse({'status': 'error', 'message': 'You cannot report your own profile.'})
    
    # Get report details
    report_type = request.POST.get('report_type')
    details = request.POST.get('details', '')
    
    # Create the report
    report = Report.objects.create(
        from_user=request.user,
        against_user=user,
        report_type=report_type,
        details=details
    )
    
    return JsonResponse({
        'status': 'success', 
        'message': 'Profile reported successfully. Our team will review your report.'
    })

# Error handling views
def handler404(request, exception):
    """
    Custom 404 error handler
    """
    return render(request, 'core/errors/404.html', status=404)


def handler500(request):
    """
    Custom 500 error handler
    """
    return render(request, 'core/errors/500.html', status=500)


def handler403(request, exception):
    """
    Custom 403 error handler
    """
    return render(request, 'core/errors/403.html', status=403)


def handler400(request, exception):
    """
    Custom 400 error handler
    """
    return render(request, 'core/errors/400.html', status=400)

def test_error(request, error_type):
    """
    A view to test different error types.
    
    Args:
        request: The HTTP request
        error_type: The type of error to trigger (404, 500, 403, 400)
    """
    if error_type == '404':
        # Raise a 404 error
        from django.http import Http404
        raise Http404("Test 404 error")
    elif error_type == '500':
        # Raise a server error
        raise Exception("Test 500 error")
    elif error_type == '403':
        # Raise a permission denied error
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Test 403 error")
    elif error_type == '400':
        # Raise a bad request error
        from django.http import HttpResponseBadRequest
        return HttpResponseBadRequest("Test 400 error")
    else:
        return HttpResponse(f"Unknown error type: {error_type}")

def error_docs(request):
    """
    View to display the error handling documentation page.
    
    Args:
        request: The HTTP request
        
    Returns:
        HttpResponse: The rendered error documentation page
    """
    return render(request, 'core/error_docs.html')

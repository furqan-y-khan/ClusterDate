import json
import requests
from django.conf import settings
from django.contrib.auth.models import User
from firebase_admin import messaging
from messaging.models import Notification
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q
import logging
from django.urls import reverse
import uuid
import math

from .models import Like, Match, Block, Profile
from messaging.models import Conversation
from payments.models import Subscription, Plan

logger = logging.getLogger(__name__)

def send_push_notification(user, title, body, data=None):
    """
    Send a push notification to a user using Firebase Cloud Messaging
    
    Parameters:
    - user: User object
    - title: Notification title
    - body: Notification body
    - data: Additional data to send with the notification
    
    Returns:
    - success: Boolean indicating if the notification was sent successfully
    - error: Error message if any
    """
    if not hasattr(user, 'profile') or not user.profile.fcm_token:
        return False, "User has no FCM token"
    
    try:
        # Create message
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=user.profile.fcm_token,
        )
        
        # Send message
        response = messaging.send(message)
        
        # Create notification in database
        Notification.objects.create(
            user=user,
            notification_type='SYSTEM',
            content=body,
        )
        
        return True, response
    except Exception as e:
        return False, str(e)

def send_match_notification(match):
    """
    Send a notification when users match
    """
    # Notify user1
    send_push_notification(
        user=match.user1,
        title="New Match!",
        body=f"You matched with {match.user2.username}!",
        data={
            "notification_type": "MATCH",
            "match_id": str(match.id),
            "user_id": str(match.user2.id),
            "username": match.user2.username,
            "url": f"/matches/"
        }
    )
    
    # Notify user2
    send_push_notification(
        user=match.user2,
        title="New Match!",
        body=f"You matched with {match.user1.username}!",
        data={
            "notification_type": "MATCH",
            "match_id": str(match.id),
            "user_id": str(match.user1.id),
            "username": match.user1.username,
            "url": f"/matches/"
        }
    )

def send_message_notification(message):
    """
    Send a notification for a new message
    """
    # Get the receiver (other participant)
    receiver = message.conversation.get_other_participant(message.sender)
    
    if not receiver:
        return False, "No receiver found"
    
    # Check if the receiver wants to receive message notifications
    if not receiver.profile.receive_message_notifications:
        return False, "Receiver has disabled message notifications"
    
    # Send notification
    return send_push_notification(
        user=receiver,
        title=f"Message from {message.sender.username}",
        body=f"{message.content[:50]}{'...' if len(message.content) > 50 else ''}",
        data={
            "notification_type": "MESSAGE",
            "conversation_id": str(message.conversation.id),
            "sender_id": str(message.sender.id),
            "sender_username": message.sender.username,
            "url": f"/messaging/conversation/{message.conversation.id}/"
        }
    )

def send_like_notification(like):
    """
    Send a notification when a user receives a like
    """
    # Check if the receiver wants to receive like notifications
    if not like.to_user.profile.receive_like_notifications:
        return False, "Receiver has disabled like notifications"
    
    # Send notification
    return send_push_notification(
        user=like.to_user,
        title="New Like!",
        body=f"{like.from_user.username} liked your profile!",
        data={
            "notification_type": "LIKE",
            "from_user_id": str(like.from_user.id),
            "from_username": like.from_user.username,
            "url": f"/profile/{like.from_user.username}/"
        }
    )

def send_call_notification(call_session):
    """
    Send a notification for an incoming call
    """
    # Send notification
    return send_push_notification(
        user=call_session.receiver,
        title=f"Incoming {call_session.call_type.title()} Call",
        body=f"{call_session.caller.username} is calling you",
        data={
            "notification_type": "CALL",
            "call_id": str(call_session.session_id),
            "caller_id": str(call_session.caller.id),
            "caller_username": call_session.caller.username,
            "call_type": call_session.call_type,
            "url": f"/video-call/room/{call_session.session_id}/"
        }
    )

def process_like_action(request, username):
    """
    Process a like action from any app
    Returns JSON response with status information
    """
    try:
        to_user = get_object_or_404(User, username=username)
        
        # Check if already liked
        if Like.objects.filter(from_user=request.user, to_user=to_user).exists():
            return JsonResponse({'status': 'already_liked'})
        
        # Create the like
        like = Like.objects.create(from_user=request.user, to_user=to_user)
        
        # Check if this creates a match
        is_match = like.create_match_if_mutual()
        
        if is_match:
            return JsonResponse({
                'status': 'match', 
                'message': f"You matched with {to_user.username}!"
            })
        
        return JsonResponse({
            'status': 'liked',
            'message': f"You liked {to_user.username}'s profile"
        })
    except Exception as e:
        logger.error(f"Error in process_like_action: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def process_unlike_action(request, username):
    """
    Process an unlike action from any app
    Returns JSON response with status information
    """
    try:
        to_user = get_object_or_404(User, username=username)
        
        # Delete the like
        Like.objects.filter(from_user=request.user, to_user=to_user).delete()
        
        # Check if there was a match and delete it
        Match.objects.filter(
            (Q(user1=request.user, user2=to_user) | Q(user1=to_user, user2=request.user))
        ).delete()
        
        return JsonResponse({
            'status': 'unliked',
            'message': f"You unliked {to_user.username}'s profile"
        })
    except Exception as e:
        logger.error(f"Error in process_unlike_action: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def start_conversation(request, username):
    """
    Start a conversation with another user
    Returns JSON response with conversation ID
    """
    try:
        recipient = get_object_or_404(User, username=username)
        
        # Check if a conversation already exists
        existing_conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=recipient
        ).first()
        
        if existing_conversation:
            return JsonResponse({
                'status': 'success',
                'conversation_id': existing_conversation.id
            })
        
        # Create a new conversation
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, recipient)
        
        return JsonResponse({
            'status': 'success',
            'conversation_id': conversation.id
        })
    except Exception as e:
        logger.error(f"Error in start_conversation: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def initiate_video_call(request, username, call_type='video'):
    """
    Initiate a video or audio call with another user from any app
    Returns a redirect to the video call room
    """
    try:
        other_user = get_object_or_404(User, username=username)
        
        # Check if users are matched
        is_matched = Match.objects.filter(
            (Q(user1=request.user) & Q(user2=other_user)) | 
            (Q(user1=other_user) & Q(user2=request.user))
        ).exists()
        
        if not is_matched:
            return JsonResponse({
                'status': 'error',
                'message': 'You can only call users you have matched with'
            }, status=403)
        
        # Check for blocks
        if Block.objects.filter(
            (Q(from_user=request.user, to_user=other_user) | 
             Q(from_user=other_user, to_user=request.user))
        ).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Cannot call this user due to blocking'
            }, status=403)
        
        # Generate a unique call ID
        call_id = uuid.uuid4()
        
        # Store call information in session
        request.session['call_info'] = {
            'call_id': str(call_id),
            'caller': request.user.username,
            'recipient': other_user.username,
            'call_type': call_type
        }
        
        # Return call initiation information
        call_url = reverse('video_call:call_room', args=[call_id])
        return JsonResponse({
            'status': 'success',
            'call_id': str(call_id),
            'call_url': call_url
        })
        
    except Exception as e:
        logger.error(f"Error in initiate_video_call: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def check_premium_access(user, feature):
    """
    Check if a user has access to a premium feature
    Returns True if they have access, False otherwise
    
    Features:
    - video_call: Video/audio calling
    - messaging: Unlimited messaging
    - advanced_search: Advanced search filters
    - profile_boost: Profile boosting
    - see_likes: See who liked you
    - hide_ads: Hide advertisements
    """
    try:
        # Check if user has an active subscription
        subscription = Subscription.objects.filter(user=user, is_active=True).first()
        
        if not subscription:
            return False
            
        # Get the plan associated with the subscription
        plan = subscription.plan
        
        # Check if the plan includes the requested feature
        if feature == 'video_call' and plan.include_video_calls:
            return True
        elif feature == 'messaging' and plan.unlimited_messages:
            return True
        elif feature == 'advanced_search' and plan.advanced_search:
            return True
        elif feature == 'profile_boost' and plan.profile_boost:
            return True
        elif feature == 'see_likes' and plan.see_who_likes_you:
            return True
        elif feature == 'hide_ads' and plan.ad_free:
            return True
            
        return False
    except Exception as e:
        logger.error(f"Error in check_premium_access: {str(e)}")
        return False
        
def get_upgrade_url(feature):
    """
    Get the URL to upgrade to access a premium feature
    """
    return reverse('payments:plan_list') + f'?feature={feature}'

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two coordinates in kilometers
    Uses the Haversine formula
    """
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of Earth in kilometers
    
    return c * r

def geocode_address(address):
    """
    Convert an address to latitude and longitude using Google Maps API
    """
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={settings.GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if data['status'] == 'OK':
            location = data['results'][0]['geometry']['location']
            return {
                'latitude': location['lat'],
                'longitude': location['lng'],
                'formatted_address': data['results'][0]['formatted_address']
            }
        else:
            logger.error(f"Geocoding error: {data['status']}")
            return None
    except Exception as e:
        logger.error(f"Error in geocode_address: {str(e)}")
        return None

def update_user_location(user, latitude, longitude):
    """
    Update the user's location in their profile
    """
    try:
        profile = Profile.objects.get(user=user)
        profile.latitude = latitude
        profile.longitude = longitude
        profile.save()
        return True
    except Exception as e:
        logger.error(f"Error in update_user_location: {str(e)}")
        return False

def find_nearby_users(user, max_distance=50, **filters):
    """
    Find users within a certain distance of the current user
    Additional filters can be passed as keyword arguments
    """
    try:
        # Get the user's profile
        profile = Profile.objects.get(user=user)
        
        if not profile.latitude or not profile.longitude:
            return []
            
        # Get all active users except the current user
        users = Profile.objects.filter(
            user__is_active=True
        ).exclude(
            user=user
        )
        
        # Apply any additional filters
        if filters:
            users = users.filter(**filters)
        
        # Find users with location data
        users = users.filter(
            latitude__isnull=False,
            longitude__isnull=False
        )
        
        # Calculate distances and filter
        result = []
        for u in users:
            distance = calculate_distance(
                profile.latitude, profile.longitude,
                u.latitude, u.longitude
            )
            
            if distance <= max_distance:
                u.distance = distance
                result.append(u)
        
        # Sort by distance (closest first)
        result.sort(key=lambda x: x.distance)
        
        return result
    except Exception as e:
        logger.error(f"Error in find_nearby_users: {str(e)}")
        return [] 
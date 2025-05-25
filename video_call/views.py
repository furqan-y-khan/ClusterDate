from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone

from core.models import Match, Block
from core.utils import initiate_video_call as core_initiate_video_call
from .models import CallSession, CallFeedback
import json
import uuid
import logging

logger = logging.getLogger(__name__)

@login_required
@require_POST
def initiate_call(request, username):
    """
    Initiate a video call with a user
    This view can be called from any app
    """
    call_type = request.POST.get('call_type', 'video')
    return core_initiate_video_call(request, username, call_type)

@login_required
def call_room(request, call_id):
    """
    Join a video call room
    """
    # Get call info from session
    call_info = request.session.get('call_info', {})
    
    # If no call info, might be joining from recipient side
    if not call_info or str(call_id) != call_info.get('call_id'):
        # Try to find a call session for this call ID
        call_session = CallSession.objects.filter(call_id=call_id).first()
        if call_session:
            if request.user.username not in [call_session.caller, call_session.recipient]:
                return HttpResponseForbidden("You are not authorized to join this call")
            
            # Update call info from the session
            call_info = {
                'call_id': str(call_id),
                'caller': call_session.caller,
                'recipient': call_session.recipient,
                'call_type': call_session.call_type
            }
        else:
            # No call info and no call session - invalid call
            return HttpResponseForbidden("Invalid call ID")
    
    # Create or update the call session
    caller_username = call_info.get('caller')
    recipient_username = call_info.get('recipient')
    call_type = call_info.get('call_type', 'video')
    
    caller = User.objects.filter(username=caller_username).first()
    recipient = User.objects.filter(username=recipient_username).first()
    
    if not caller or not recipient:
        return HttpResponseForbidden("Invalid caller or recipient")
    
    call_session, created = CallSession.objects.update_or_create(
        call_id=call_id,
        defaults={
            'caller': caller_username,
            'recipient': recipient_username,
            'call_type': call_type,
            'status': 'initiated' if created else 'active'
        }
    )
    
    return render(request, 'video_call/call_room.html', {
        'call_id': call_id,
        'call_type': call_type,
        'caller': caller,
        'recipient': recipient,
        'is_caller': request.user.username == caller_username,
        'turn_credentials': {
            'username': settings.TURN_SERVER_USERNAME,
            'credential': settings.TURN_SERVER_CREDENTIAL,
            'urls': [settings.TURN_SERVER_URL]
        }
    })

@login_required
@require_POST
def end_call(request, call_id):
    """
    End a video call
    """
    call_session = get_object_or_404(CallSession, call_id=call_id)
    
    # Check if user is in the call
    if request.user.username not in [call_session.caller, call_session.recipient]:
        return HttpResponseForbidden("You are not authorized to end this call")
    
    call_session.status = 'ended'
    call_session.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('video_call:call_history')

@login_required
@require_POST
def accept_call(request, call_id):
    """
    Accept an incoming call
    """
    call_session = get_object_or_404(CallSession, call_id=call_id)
    
    # Check if user is the recipient
    if request.user.username != call_session.recipient:
        return HttpResponseForbidden("You are not authorized to accept this call")
    
    call_session.status = 'active'
    call_session.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'call_url': reverse('video_call:call_room', args=[call_id])
        })
    
    return redirect('video_call:call_room', call_id=call_id)

@login_required
@require_POST
def reject_call(request, call_id):
    """
    Reject an incoming call
    """
    call_session = get_object_or_404(CallSession, call_id=call_id)
    
    # Check if user is the recipient
    if request.user.username != call_session.recipient:
        return HttpResponseForbidden("You are not authorized to reject this call")
    
    call_session.status = 'rejected'
    call_session.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('video_call:call_history')

@login_required
def call_history(request):
    """
    View call history
    """
    username = request.user.username
    
    # Get all calls where the user is either caller or recipient
    calls = CallSession.objects.filter(
        Q(caller=username) | Q(recipient=username)
    ).order_by('-created_at')
    
    return render(request, 'video_call/call_history.html', {'calls': calls})

@login_required
@require_POST
def call_feedback(request, call_id):
    """
    Submit feedback for a call
    """
    call_session = get_object_or_404(CallSession, call_id=call_id)
    
    # Check if user was in the call
    if request.user.username not in [call_session.caller, call_session.recipient]:
        return HttpResponseForbidden("You were not in this call")
    
    # Get feedback data
    rating = request.POST.get('rating')
    comments = request.POST.get('comments', '')
    
    if not rating:
        return JsonResponse({'status': 'error', 'message': 'Rating is required'}, status=400)
    
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid rating'}, status=400)
    
    # Create the feedback
    feedback = CallFeedback.objects.create(
        call_session=call_session,
        user=request.user,
        rating=rating,
        comments=comments
    )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('video_call:call_history') 
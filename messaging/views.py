from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q, Max, F, ExpressionWrapper, fields
from django.db.models.functions import Coalesce
from .models import Conversation, Message, Notification
from core.models import Match, Block, MatchRequest
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from core.utils import start_conversation as core_start_conversation
import json
import logging

logger = logging.getLogger(__name__)

@login_required
def inbox(request):
    """View all conversations"""
    # Get conversations
    conversations = []
    conversation_objs = Conversation.objects.filter(participants=request.user).prefetch_related('participants')
    
    # For each conversation, get the other participant and last message
    for conversation in conversation_objs:
        other_user = conversation.participants.exclude(id=request.user.id).first()
        last_message = Message.objects.filter(conversation=conversation).order_by('-timestamp').first()
        unread_count = Message.objects.filter(conversation=conversation, is_read=False).exclude(sender=request.user).count()
        
        conversations.append({
            'id': conversation.id,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': unread_count
        })
    
    # Sort conversations by last message timestamp (newest first)
    conversations.sort(key=lambda x: x['last_message'].timestamp if x['last_message'] else timezone.now(), reverse=True)
    
    # Get pending match requests
    pending_matches = []
    pending_match_requests = MatchRequest.objects.filter(to_user=request.user, status='PENDING')
    for match_req in pending_match_requests:
        pending_matches.append(match_req.from_user)
    
    return render(request, 'messaging/inbox.html', {
        'conversations': conversations,
        'pending_matches': pending_matches
    })

@login_required
def conversation_view(request, conversation_id):
    """View a specific conversation and send messages"""
    # Get the conversation
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    other_user = conversation.participants.exclude(id=request.user.id).first()
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            
            # If this is AJAX, return message data
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': {
                        'id': message.id,
                        'content': message.content,
                        'timestamp': message.timestamp.strftime('%I:%M %p'),
                        'sender_id': message.sender.id
                    }
                })
            
            return redirect('messaging:conversation', conversation_id=conversation.id)
    
    # Mark all unread messages in this conversation as read
    unread_messages = Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=request.user)
    
    for message in unread_messages:
        message.is_read = True
        message.save()
    
    # Get all messages for this conversation
    messages = Message.objects.filter(conversation=conversation).order_by('timestamp')
    
    # Get conversations for sidebar
    sidebar_conversations = []
    conversation_objs = Conversation.objects.filter(participants=request.user).prefetch_related('participants')
    
    # For each conversation, get the other participant and last message
    for conv in conversation_objs:
        conv_other_user = conv.participants.exclude(id=request.user.id).first()
        last_message = Message.objects.filter(conversation=conv).order_by('-timestamp').first()
        unread_count = Message.objects.filter(conversation=conv, is_read=False).exclude(sender=request.user).count()
        
        sidebar_conversations.append({
            'id': conv.id,
            'other_user': conv_other_user,
            'last_message': last_message,
            'unread_count': unread_count
        })
    
    # Sort conversations by last message timestamp (newest first)
    sidebar_conversations.sort(key=lambda x: x['last_message'].timestamp if x['last_message'] else timezone.now(), reverse=True)
    
    # Get pending match requests
    pending_matches = []
    pending_match_requests = MatchRequest.objects.filter(to_user=request.user, status='PENDING')
    for match_req in pending_match_requests:
        pending_matches.append(match_req.from_user)
    
    return render(request, 'messaging/inbox.html', {
        'conversations': sidebar_conversations,
        'active_conversation': {
            'id': conversation.id,
            'other_user': other_user
        },
        'messages': messages,
        'pending_matches': pending_matches
    })

@login_required
@require_POST
def start_conversation(request, username):
    """
    Start a conversation with a user
    Can be called from any app via AJAX
    """
    return core_start_conversation(request, username)

@login_required
def notifications(request):
    """View all notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'messaging/notifications.html', {'notifications': notifications})

@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('messaging:notifications')

@login_required
@require_POST
def mark_all_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('messaging:notifications')

@login_required
@require_POST
def delete_conversation(request, conversation_id):
    """Delete a conversation"""
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    conversation.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('messaging:inbox')

@login_required
def notification_count(request):
    """Get the number of unread notifications"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})

@login_required
def inbox_refresh(request):
    """AJAX endpoint to refresh the inbox"""
    conversations = []
    conversation_objs = Conversation.objects.filter(participants=request.user).prefetch_related('participants')
    
    for conversation in conversation_objs:
        other_user = conversation.participants.exclude(id=request.user.id).first()
        last_message = Message.objects.filter(conversation=conversation).order_by('-timestamp').first()
        unread_count = Message.objects.filter(conversation=conversation, is_read=False).exclude(sender=request.user).count()
        
        conversations.append({
            'id': conversation.id,
            'other_user': {
                'id': other_user.id,
                'username': other_user.username,
                'full_name': other_user.get_full_name() or other_user.username,
                'profile_picture': other_user.profile.profile_picture.url if other_user.profile.profile_picture else None
            },
            'last_message': {
                'content': last_message.content if last_message else "No messages yet",
                'timestamp': last_message.timestamp.strftime('%b %d, %Y, %I:%M %p') if last_message else None,
                'is_read': last_message.is_read if last_message else True
            },
            'unread_count': unread_count
        })
    
    # Sort conversations by last message timestamp (newest first)
    conversations.sort(key=lambda x: x['last_message']['timestamp'] if x['last_message']['timestamp'] else '', reverse=True)
    
    # Get pending match requests
    pending_matches = []
    pending_match_requests = MatchRequest.objects.filter(to_user=request.user, status='PENDING')
    for match_req in pending_match_requests:
        user = match_req.from_user
        pending_matches.append({
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'profile_picture': user.profile.profile_picture.url if user.profile.profile_picture else None
        })
    
    return JsonResponse({
        'conversations': conversations,
        'pending_matches': pending_matches
    })

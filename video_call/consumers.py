import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import CallSession
from django.utils import timezone

class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.call_id = self.scope['url_route']['kwargs']['call_id']
        self.call_group_name = f'call_{self.call_id}'
        
        # Join call group
        await self.channel_layer.group_add(
            self.call_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave call group
        await self.channel_layer.group_discard(
            self.call_group_name,
            self.channel_name
        )
        
        # End call if it's ongoing
        await self.end_call_if_ongoing()
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'offer':
            await self.handle_offer(data)
        elif message_type == 'answer':
            await self.handle_answer(data)
        elif message_type == 'ice_candidate':
            await self.handle_ice_candidate(data)
        elif message_type == 'end_call':
            await self.handle_end_call(data)
        elif message_type == 'accept_call':
            await self.handle_accept_call(data)
        elif message_type == 'reject_call':
            await self.handle_reject_call(data)
    
    async def handle_offer(self, data):
        # Send offer to the group
        await self.channel_layer.group_send(
            self.call_group_name,
            {
                'type': 'call_offer',
                'offer': data['offer'],
                'caller': self.user.username
            }
        )
    
    async def handle_answer(self, data):
        # Send answer to the group
        await self.channel_layer.group_send(
            self.call_group_name,
            {
                'type': 'call_answer',
                'answer': data['answer'],
                'answerer': self.user.username
            }
        )
    
    async def handle_ice_candidate(self, data):
        # Send ICE candidate to the group
        await self.channel_layer.group_send(
            self.call_group_name,
            {
                'type': 'ice_candidate',
                'candidate': data['candidate'],
                'sender': self.user.username
            }
        )
    
    async def handle_end_call(self, data):
        # End the call
        await self.end_call_if_ongoing()
        
        # Notify the group that the call has ended
        await self.channel_layer.group_send(
            self.call_group_name,
            {
                'type': 'call_ended',
                'ended_by': self.user.username
            }
        )
    
    async def handle_accept_call(self, data):
        # Accept the call
        await self.accept_call()
        
        # Notify the group that the call has been accepted
        await self.channel_layer.group_send(
            self.call_group_name,
            {
                'type': 'call_accepted',
                'accepted_by': self.user.username
            }
        )
    
    async def handle_reject_call(self, data):
        # Reject the call
        await self.reject_call()
        
        # Notify the group that the call has been rejected
        await self.channel_layer.group_send(
            self.call_group_name,
            {
                'type': 'call_rejected',
                'rejected_by': self.user.username
            }
        )
    
    # Handlers for messages sent by the channel layer
    async def call_offer(self, event):
        # Send offer to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'offer',
            'offer': event['offer'],
            'caller': event['caller']
        }))
    
    async def call_answer(self, event):
        # Send answer to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'answer',
            'answer': event['answer'],
            'answerer': event['answerer']
        }))
    
    async def ice_candidate(self, event):
        # Send ICE candidate to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'ice_candidate',
            'candidate': event['candidate'],
            'sender': event['sender']
        }))
    
    async def call_ended(self, event):
        # Send call ended notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'call_ended',
            'ended_by': event['ended_by']
        }))
    
    async def call_accepted(self, event):
        # Send call accepted notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'call_accepted',
            'accepted_by': event['accepted_by']
        }))
    
    async def call_rejected(self, event):
        # Send call rejected notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'call_rejected',
            'rejected_by': event['rejected_by']
        }))
    
    # Database operations
    @database_sync_to_async
    def end_call_if_ongoing(self):
        try:
            call_session = CallSession.objects.get(session_id=self.call_id)
            if call_session.status == 'ONGOING':
                call_session.end_call()
            return True
        except CallSession.DoesNotExist:
            return False
    
    @database_sync_to_async
    def accept_call(self):
        try:
            call_session = CallSession.objects.get(session_id=self.call_id)
            call_session.accept_call()
            return True
        except CallSession.DoesNotExist:
            return False
    
    @database_sync_to_async
    def reject_call(self):
        try:
            call_session = CallSession.objects.get(session_id=self.call_id)
            call_session.reject_call()
            return True
        except CallSession.DoesNotExist:
            return False 
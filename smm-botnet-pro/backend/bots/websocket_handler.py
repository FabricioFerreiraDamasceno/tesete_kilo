"""
WebSocket Handler - Manages WebSocket connections for real-time updates.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User, AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .models import Order, BotAccount

logger = logging.getLogger(__name__)


class BotConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for bot and order updates."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        # Extract token from query string
        query_string = self.scope['query_string'].decode()
        token = None
        
        for param in query_string.split('&'):
            if param.startswith('token='):
                token = param.split('=')[1]
                break
        
        # Authenticate user
        self.user = await self.get_user_from_token(token)
        if self.user is None or isinstance(self.user, AnonymousUser):
            logger.warning("WebSocket connection rejected: invalid or missing token")
            await self.close()
            return
        
        # Join user-specific group
        self.user_group_name = f'user_{self.user.id}'
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        # Join bots group for general updates
        await self.channel_layer.group_add(
            'bots_updates',
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"WebSocket connected for user {self.user.username}")
        
        # Send initial data
        await self.send_initial_data()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave groups
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
        
        await self.channel_layer.group_discard(
            'bots_updates',
            self.channel_name
        )
        
        logger.info(f"WebSocket disconnected for user {getattr(self.user, 'username', 'unknown')}")
    
    async def receive(self, text_data):
        """Handle messages from WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            elif message_type == 'get_order_status':
                order_id = data.get('order_id')
                if order_id:
                    await self.send_order_status(order_id)
            elif message_type == 'get_bot_status':
                await self.send_bot_status()
            else:
                logger.warning(f"Unknown WebSocket message type: {message_type}")
        
        except json.JSONDecodeError:
            logger.error("Invalid JSON received in WebSocket")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
    
    # Handler methods for messages sent to the consumer
    async def order_update(self, event):
        """Send order update to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'order_update',
            'data': event['data']
        }))
    
    async def bot_status_update(self, event):
        """Send bot status update to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'bot_status_update',
            'data': event['data']
        }))
    
    async def system_alert(self, event):
        """Send system alert to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'system_alert',
            'data': event['data']
        }))
    
    # Helper methods
    @database_sync_to_async
    def get_user_from_token(self, token: str) -> User:
        """Get user from JWT token."""
        if not token:
            return AnonymousUser()
        
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            return User.objects.get(id=user_id)
        except (InvalidToken, TokenError, User.DoesNotExist) as e:
            logger.debug(f"Invalid token: {e}")
            return AnonymousUser()
    
    @database_sync_to_async
    def get_order_data(self, order_id: int) -> dict:
        """Get order data for sending via WebSocket."""
        try:
            order = Order.objects.select_related('user').get(id=order_id, user=self.user)
            return {
                'id': order.id,
                'target_username': order.target_username,
                'quantity': order.quantity,
                'delivered': order.delivered,
                'status': order.status,
                'progress_percentage': (order.delivered / order.quantity * 100) if order.quantity > 0 else 0,
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat(),
            }
        except Order.DoesNotExist:
            return {}
    
    @database_sync_to_async
    def get_bot_data(self) -> list:
        """Get bot data for sending via WebSocket."""
        bots = BotAccount.objects.filter(is_active=True)
        return [
            {
                'id': bot.id,
                'username': bot.username,
                'followers_count': bot.followers_count,
                'daily_follows': bot.daily_follows,
                'max_follows': bot.max_follows,
                'health_score': bot.health_score,
                'is_active': bot.is_active,
            }
            for bot in bots
        ]
    
    async def send_initial_data(self):
        """Send initial data when WebSocket connects."""
        bot_data = await self.get_bot_data()
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'data': {
                'bots': bot_data
            }
        }))
    
    async def send_order_status(self, order_id: int):
        """Send status of a specific order."""
        order_data = await self.get_order_data(order_id)
        if order_data:
            await self.send(text_data=json.dumps({
                'type': 'order_status',
                'data': order_data
            }))
    
    async def send_bot_status(self):
        """Send status of all bots."""
        bot_data = await self.get_bot_data()
        await self.send(text_data=json.dumps({
            'type': 'bot_status',
            'data': {
                'bots': bot_data
            }
        }))


# WebSocket URL patterns
websocket_urlpatterns = [
    # Note: In Django Channels 3+, we define websocket URLs in routing.py
    # This is kept for compatibility with the structure
]
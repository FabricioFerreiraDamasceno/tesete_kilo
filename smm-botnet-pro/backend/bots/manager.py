"""
Bot Manager - Core logic for managing Instagram bot operations.
"""

import heapq
import logging
from typing import List, Dict, Optional, Tuple
from django.utils import timezone
from datetime import timedelta
from .models import BotAccount, Order, FollowAction
from .priority_queue import PriorityQueue
from .smart_targeting import SmartTargetingEngine
from .dynamic_limiter import DynamicRateLimiter
from .smart_retry import SmartRetryHandler
from .redis_cache import RedisCache
from .connection_pool import ConnectionPool
from .batch_processor import BatchProcessor
from .dynamic_pricing import DynamicPricingEngine
from .reputation_system import ReputationSystem
from .monitoring import BotMonitor
from .analytics import AnalyticsEngine

logger = logging.getLogger(__name__)


class BotManager:
    """Main coordinator for all bot operations."""
    
    def __init__(self):
        self.priority_queue = PriorityQueue()
        self.targeting_engine = SmartTargetingEngine()
        self.rate_limiter = DynamicRateLimiter()
        self.retry_handler = SmartRetryHandler()
        self.cache = RedisCache()
        self.connection_pool = ConnectionPool()
        self.batch_processor = BatchProcessor()
        self.pricing_engine = DynamicPricingEngine()
        self.reputation_system = ReputationSystem()
        self.monitor = BotMonitor()
        self.analytics = AnalyticsEngine()
        self._is_running = False
    
    def start_processing(self):
        """Start the bot processing loop."""
        self._is_running = True
        logger.info("Bot Manager started processing")
        
        # In a real implementation, this would run in a separate thread/process
        # For now, we'll just initialize components
        self._initialize_components()
    
    def stop_processing(self):
        """Stop the bot processing loop."""
        self._is_running = False
        logger.info("Bot Manager stopped processing")
    
    def _initialize_components(self):
        """Initialize all components."""
        self.cache.connect()
        self.connection_pool.initialize()
        logger.info("Bot Manager components initialized")
    
    def add_order_to_queue(self, order: Order):
        """Add an order to the priority queue."""
        priority_score = self._calculate_priority_score(order)
        self.priority_queue.push(order, priority_score)
        logger.info(f"Order {order.id} added to queue with priority {priority_score}")
    
    def _calculate_priority_score(self, order: Order) -> float:
        """Calculate priority score for an order."""
        # Base priority from order (0, 1, 2)
        base_priority = order.priority
        
        # Urgency factor: orders >5000 or delayed >24h get boost
        urgency_bonus = 0.0
        if order.quantity > 5000:
            urgency_bonus += 1.0
        
        delay_hours = (timezone.now() - order.created_at).total_seconds() / 3600
        if delay_hours > 24:
            urgency_bonus += 1.0
        
        # Client reputation factor
        try:
            reputation_score = self.reputation_system.get_user_score(order.user.username)
            reputation_factor = reputation_score / 100.0  # 0-1
        except Exception:
            reputation_factor = 0.5  # Default if not found
        
        # Final score: higher = more priority
        return base_priority + urgency_bonus + (reputation_factor * 0.5)
    
    def process_next_order(self) -> Optional[Order]:
        """Get and process the next order from the queue."""
        if not self._is_running:
            return None
            
        order = self.priority_queue.pop()
        if not order:
            return None
        
        logger.info(f"Processing order {order.id} for @{order.target_username}")
        
        try:
            # Update order status
            order.status = 'processing'
            order.save()
            
            # Get targeting recommendations
            targets = self.targeting_engine.get_target_users(
                order.target_username, 
                order.quantity
            )
            
            # Distribute actions among available bots
            self._distribute_actions(order, targets)
            
            # Mark order as completed
            order.status = 'completed'
            order.completed_at = timezone.now()
            order.delivered = order.quantity  # In real app, this would be actual count
            order.save()
            
            # Update analytics
            self.analytics.record_order_completion(order)
            
            return order
            
        except Exception as e:
            logger.error(f"Error processing order {order.id}: {str(e)}")
            order.status = 'failed'
            order.save()
            return None
    
    def _distribute_actions(self, order: Order, targets: List[str]):
        """Distribute follow actions among available bots."""
        # Get active bots with available capacity
        available_bots = BotAccount.objects.filter(
            is_active=True,
            daily_follows__lt=models.F('max_follows')
        ).order_by('-health_score')
        
        if not available_bots.exists():
            logger.warning("No available bots for processing")
            return
        
        # Calculate actions per bot
        actions_per_bot = max(1, order.quantity // len(available_bots))
        remaining_actions = order.quantity % len(available_bots)
        
        bot_index = 0
        actions_assigned = 0
        
        for bot in available_bots:
            # Calculate how many actions this bot should perform
            bot_actions = actions_per_bot
            if bot_index < remaining_actions:
                bot_actions += 1
            
            # Ensure we don't exceed bot's daily limit
            max_for_bot = bot.max_follows - bot.daily_follows
            bot_actions = min(bot_actions, max_for_bot)
            
            if bot_actions <= 0:
                bot_index += 1
                continue
            
            # Get rate limit for this bot
            rate_limit = self.rate_limiter.get_limit(bot)
            actual_actions = min(bot_actions, rate_limit)
            
            # Select targets for this bot
            bot_targets = targets[actions_assigned:actions_assigned + actual_actions]
            
            # Execute actions
            self._execute_bot_actions(bot, order, bot_targets)
            
            actions_assigned += actual_actions
            bot_index += 1
            
            if actions_assigned >= order.quantity:
                break
    
    def _execute_bot_actions(self, bot: BotAccount, order: Order, targets: List[str]):
        """Execute follow actions for a specific bot."""
        for target in targets:
            if not self._is_running:
                break
                
            # Check if we should use smart retry
            action_success = False
            error_msg = None
            
            try:
                # Try the follow operation with retry logic
                action_success = self.retry_handler.execute_with_retry(
                    lambda: self._perform_follow(bot, target),
                    max_attempts=3
                )
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Follow failed for @{target}: {error_msg}")
            
            # Record the action
            FollowAction.objects.create(
                bot=bot,
                order=order,
                target_user=target,
                success=action_success,
                error_message=error_msg
            )
            
            # Update bot stats if successful
            if action_success:
                bot.daily_follows += 1
                bot.save(update_fields=['daily_follows'])
                
                # Add to batch processor for efficient DB updates
                self.batch_processor.add_follow_action(bot.id, target)
            else:
                # Apply dynamic rate limiting penalties
                self.rate_limiter.apply_penalty(bot)
            
            # Small delay between actions (simulated)
            # In real implementation, this would be handled by the retry handler
            import time
            time.sleep(0.1)  # Simplified for example
    
    def _perform_follow(self, bot: BotAccount, target: str) -> bool:
        """Perform a single follow operation."""
        if getattr(settings, 'SIMULATION_MODE', True):
            # Simulated mode - just log and return success
            logger.info(f"SIMULATION: {bot.username} following @{target}")
            return True
        
        # Real implementation would use the InstagramBot class
        from .instagram import InstagramBot
        
        ig_bot = InstagramBot(bot)
        if not ig_bot.login():
            return False
        
        return ig_bot.follow_user(target)
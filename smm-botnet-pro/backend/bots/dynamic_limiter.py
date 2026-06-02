"""
Dynamic Rate Limiter - Calculates optimal follow limits for each bot.
"""

import logging
from typing import Optional
from django.utils import timezone
from datetime import timedelta
from .models import BotAccount

logger = logging.getLogger(__name__)


class DynamicRateLimiter:
    """Calculates dynamic follow limits for bots based on various factors."""
    
    def __init__(self):
        self.base_limits = {
            'new': 30,      # Accounts < 1 month old
            'established': 70,  # Accounts 1-6 months old
            'mature': 150   # Accounts > 6 months old
        }
    
    def get_limit(self, bot: BotAccount) -> int:
        """
        Calculate the dynamic follow limit for a bot.
        Returns the maximum number of follows allowed per day.
        """
        # Start with base limit based on account age
        base_limit = self._get_base_limit(bot)
        
        # Apply health score multiplier (0.5 to 1.5)
        health_multiplier = max(0.5, min(1.5, bot.health_score / 100.0))
        
        # Apply success rate multiplier
        success_multiplier = self._get_success_multiplier(bot)
        
        # Apply time-of-day factor (more active during peak hours)
        time_multiplier = self._get_time_multiplier()
        
        # Apply recent penalty multiplier (if bot has been failing)
        penalty_multiplier = self._get_penalty_multiplier(bot)
        
        # Calculate final limit
        limit = base_limit * health_multiplier * success_multiplier * time_multiplier * penalty_multiplier
        
        # Ensure reasonable bounds
        limit = max(10, min(200, int(limit)))
        
        logger.debug(f"Dynamic limit for @{bot.username}: {limit} "
                    f"(base:{base_limit}, health:{health_multiplier:.2f}, "
                    f"success:{success_multiplier:.2f}, time:{time_multiplier:.2f}, "
                    f"penalty:{penalty_multiplier:.2f})")
        
        return limit
    
    def _get_base_limit(self, bot: BotAccount) -> int:
        """Get base limit based on account age."""
        # In a real implementation, we would check account creation date
        # For simulation, we'll use followers count as a proxy
        if bot.followers_count < 1000:
            return self.base_limits['new']
        elif bot.followers_count < 10000:
            return self.base_limits['established']
        else:
            return self.base_limits['mature']
    
    def _get_success_multiplier(self, bot: BotAccount) -> float:
        """Get multiplier based on recent success rate."""
        # Get recent follow actions (last 24 hours)
        yesterday = timezone.now() - timedelta(days=1)
        recent_actions = bot.followaction_set.filter(
            followed_at__gte=yesterday
        )
        
        if not recent_actions.exists():
            return 1.0  # No data, assume average
        
        total = recent_actions.count()
        successful = recent_actions.filter(success=True).count()
        
        if total == 0:
            return 1.0
        
        success_rate = successful / total
        
        # Convert success rate to multiplier (0.5 to 1.5)
        # 0% success -> 0.5x, 100% success -> 1.5x
        return 0.5 + success_rate
    
    def _get_time_multiplier(self) -> float:
        """Get multiplier based on time of day (peak hours)."""
        hour = timezone.now().hour
        
        # Peak hours: 9-11 AM, 2-4 PM, 7-9 PM (local time simplified)
        if 9 <= hour <= 11 or 14 <= hour <= 16 or 19 <= hour <= 21:
            return 1.2  # 20% boost during peak hours
        elif 22 <= hour <= 6:  # Night hours
            return 0.7  # 30% reduction at night
        else:
            return 1.0  # Normal hours
    
    def _get_penalty_multiplier(self, bot: BotAccount) -> float:
        """Get penalty multiplier based on recent failures."""
        # Get recent failed actions
        yesterday = timezone.now() - timedelta(hours=6)
        recent_failed = bot.followaction_set.filter(
            followed_at__gte=yesterday,
            success=False
        ).count()
        
        # Apply exponential penalty for failures
        if recent_failed == 0:
            return 1.0
        elif recent_failed <= 5:
            return 0.9  # 10% reduction
        elif recent_failed <= 15:
            return 0.7  # 30% reduction
        else:
            return 0.5  # 50% reduction for many failures
    
    def apply_penalty(self, bot: BotAccount):
        """Apply a temporary penalty to a bot due to rate limiting or blocks."""
        # In a real implementation, we might store penalty timestamps
        # For now, we'll just log it
        logger.warning(f"Applying penalty to bot @{bot.username}")
        # The penalty is applied dynamically in get_limit via _get_penalty_multiplier


# Global instance
rate_limiter = DynamicRateLimiter()
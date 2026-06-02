"""
Smart Targeting Engine - Identifies ideal users to follow based on niche and engagement.
"""

import logging
import random
from typing import List, Dict, Optional
from django.core.cache import cache
from django.conf import settings
import hashlib

logger = logging.getLogger(__name__)


class SmartTargetingEngine:
    """Engine for identifying high-propability users to follow."""
    
    # Niche keywords for classification
    NICHE_KEYWORDS = {
        'fashion': ['fashion', 'style', 'outfit', 'clothes', 'wear', 'model', 'designer'],
        'fitness': ['fitness', 'gym', 'workout', 'fit', 'health', 'training', 'muscle'],
        'beauty': ['beauty', 'makeup', 'skincare', 'beautiful', 'cosmetics', 'glam'],
        'travel': ['travel', 'traveling', 'wanderlust', 'adventure', 'trip', 'vacation'],
        'food': ['food', 'foodie', 'cooking', 'recipe', 'chef', 'restaurant', 'yummy'],
        'tech': ['tech', 'technology', 'gadgets', 'coding', 'programming', 'ai', 'software'],
        'business': ['business', 'entrepreneur', 'marketing', 'sales', 'startup', 'ceo'],
        'lifestyle': ['lifestyle', 'daily', 'life', 'blog', 'vlog', 'influencer']
    }
    
    def __init__(self):
        self.cache_timeout = 300  # 5 minutes
    
    def get_target_users(self, target_username: str, quantity: int) -> List[str]:
        """
        Get target users to follow based on the target account's niche.
        Returns a list of usernames.
        """
        # Check cache first
        cache_key = f"targeting:{target_username}:{quantity}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for targeting {target_username}")
            return cached_result
        
        # Determine niche of target account
        niche = self._detect_niche(target_username)
        logger.info(f"Target @{target_username} classified as niche: {niche}")
        
        # Get users based on niche
        if getattr(settings, 'SIMULATION_MODE', True):
            users = self._get_simulated_targets(niche, quantity)
        else:
            users = self._get_real_targets(target_username, niche, quantity)
        
        # Cache the result
        cache.set(cache_key, users, self.cache_timeout)
        logger.debug(f"Cached targeting result for {target_username}")
        
        return users
    
    def _detect_niche(self, username: str) -> str:
        """Detect the niche of a username based on profile information."""
        # In simulation mode, we'll return a random niche or based on username
        if getattr(settings, 'SIMULATION_MODE', True):
            # Simple hash-based deterministic niche for simulation
            hash_value = int(hashlib.md5(username.encode()).hexdigest(), 16)
            niches = list(self.NICHE_KEYWORDS.keys())
            return niches[hash_value % len(niches)]
        
        # Real implementation would fetch user info and analyze bio, posts, etc.
        user_info = self._get_user_info(username)
        if not user_info:
            return 'lifestyle'  # Default niche
        
        bio = user_info.get('biography', '').lower()
        # Check for niche keywords in bio
        for niche, keywords in self.NICHE_KEYWORDS.items():
            if any(keyword in bio for keyword in keywords):
                return niche
        
        # If no match, check recent captions (simplified)
        return 'lifestyle'
    
    def _get_simulated_targets(self, niche: str, quantity: int) -> List[str]:
        """Generate simulated target users for a niche."""
        users = []
        for i in range(quantity):
            # Generate realistic usernames based on niche
            if niche == "fashion":
                users.append(f"style_{random.randint(1000, 9999)}_{chr(random.randint(97, 122))}")
            elif niche == "fitness":
                users.append(f"fitlife_{random.randint(100, 999)}")
            elif niche == "beauty":
                users.append(f"glam_{random.randint(1000, 9999)}")
            elif niche == "travel":
                users.append(f"wanderlust_{random.randint(100, 999)}")
            elif niche == "food":
                users.append(f"foodie_{random.randint(1000, 9999)}")
            elif niche == "tech":
                users.append(f"code_{random.randint(100, 999)}")
            elif niche == "business":
                users.append(f"ceo_{random.randint(100, 999)}")
            else:
                users.append(f"user_{random.randint(1000, 9999)}")
        
        # Add some delay to simulate processing
        import time
        time.sleep(0.1)
        
        return users
    
    def _get_real_targets(self, target_username: str, niche: str, quantity: int) -> List[str]:
        """Get real target users from Instagram (placeholder)."""
        # In real implementation, this would:
        # 1. Get followers/following of target account
        # 2. Filter by engagement rate
        # 3. Filter by activity level
        # 4. Sort by follow-back probability
        # 5. Return top quantity users
        
        # For now, return empty list to indicate not implemented
        logger.warning("Real targeting not implemented - returning empty list")
        return []
    
    def _get_user_info(self, username: str) -> Optional[Dict]:
        """Get user information from Instagram (placeholder)."""
        if getattr(settings, 'SIMULATION_MODE', True):
            return {
                'username': username,
                'biography': f"Official {username} account",
                'followers_count': random.randint(1000, 100000),
                'follows_count': random.randint(50, 1500),
                'media_count': random.randint(10, 1000),
            }
        
        # Real implementation would use Instagram API
        return None
    
    def calculate_follow_probability(self, user_info: Dict) -> float:
        """
        Calculate the probability that a user will follow back.
        Score from 0.0 to 1.0.
        """
        if not user_info:
            return 0.1
        
        followers = user_info.get('followers_count', 0)
        following = user_info.get('follows_count', 0)
        posts = user_info.get('media_count', 0)
        
        # Avoid division by zero
        if following == 0:
            following = 1
        
        # Follower/following ratio (ideal is ~1.0 or higher)
        ratio_score = min(followers / following, 2.0) / 2.0  # Normalize to 0-1
        
        # Activity score (based on posts)
        activity_score = min(posts / 100, 1.0)  # Normalize assuming 100+ posts is active
        
        # Engagement would be ideal here, but we don't have it in basic info
        engagement_estimate = 0.05  # Default 5% engagement
        
        # Combined score
        score = (ratio_score * 0.4) + (activity_score * 0.3) + (engagement_estimate * 0.3)
        
        return min(max(score, 0.0), 1.0)  # Clamp to 0-1


# Global instance
targeting_engine = SmartTargetingEngine()
"""
Instagram Bot Simulation - Handles Instagram API interactions.
In simulation mode, this just logs actions. In real mode, 
it would use instagrapi or similar library.
"""

import random
import time
import logging
from typing import Optional, List
from django.conf import settings

logger = logging.getLogger(__name__)


class InstagramBot:
    """Simulates Instagram bot operations."""
    
    def __init__(self, bot_account):
        self.bot_account = bot_account
        self.username = bot_account.username
        self.password = bot_account.password
        self.proxy = bot_account.proxy
        self.is_logged_in = False
        self.session = None
    
    def login(self) -> bool:
        """Simulate logging into Instagram."""
        if getattr(settings, 'SIMULATION_MODE', True):
            logger.info(f"SIMULATION: Logging in as {self.username}")
            self.is_logged_in = True
            # Simulate network delay
            time.sleep(random.uniform(0.5, 1.5))
            return True
        
        # Real implementation would go here
        # Example with instagrapi:
        # from instagrapi import Client
        # self.session = Client()
        # if self.proxy:
        #     self.session.set_proxy(self.proxy)
        # try:
        #     self.session.login(self.username, self.password)
        #     self.is_logged_in = True
        #     return True
        # except Exception as e:
        #     logger.error(f"Login failed for {self.username}: {e}")
        #     return False
        
        return False
    
    def follow_user(self, target_username: str) -> bool:
        """Simulate following a user."""
        if not self.is_logged_in:
            logger.error("Not logged in")
            return False
        
        if getattr(settings, 'SIMULATION_MODE', True):
            logger.info(f"SIMULATION: {self.username} following @{target_username}")
            # Simulate random failure rate (5% failure rate)
            success = random.random() > 0.05
            # Simulate network delay
            time.sleep(random.uniform(1.0, 3.0))
            return success
        
        # Real implementation would go here
        # try:
        #     self.session.user_follow_by_username(target_username)
        #     return True
        # except Exception as e:
        #     logger.error(f"Follow failed for {self.username} -> {target_username}: {e}")
        #     return False
        
        return False
    
    def unfollow_user(self, target_username: str) -> bool:
        """Simulate unfollowing a user."""
        if not self.is_logged_in:
            logger.error("Not logged in")
            return False
        
        if getattr(settings, 'SIMULATION_MODE', True):
            logger.info(f"SIMULATION: {self.username} unfollowing @{target_username}")
            # Simulate network delay
            time.sleep(random.uniform(1.0, 3.0))
            return True
        
        # Real implementation would go here
        return False
    
    def get_random_users(self, niche: str, count: int = 100) -> List[str]:
        """Get random users from a specific niche."""
        if getattr(settings, 'SIMULATION_MODE', True):
            logger.info(f"SIMULATION: Getting {count} random users for niche '{niche}'")
            # Generate fake usernames
            users = []
            for i in range(count):
                # Create realistic-looking usernames based on niche
                if niche == "fashion":
                    users.append(f"fashion_{random.randint(1000, 9999)}")
                elif niche == "fitness":
                    users.append(f"fit_{random.randint(1000, 9999)}")
                elif niche == "beauty":
                    users.append(f"beauty_{random.randint(1000, 9999)}")
                else:
                    users.append(f"user_{random.randint(1000, 9999)}")
            return users
        
        # Real implementation would search for users by hashtags, etc.
        return []
    
    def get_user_info(self, username: str) -> Optional[dict]:
        """Get information about a user."""
        if getattr(settings, 'SIMULATION_MODE', True):
            logger.info(f"SIMULATION: Getting info for @{username}")
            return {
                'username': username,
                'followers': random.randint(100, 50000),
                'following': random.randint(50, 1500),
                'posts': random.randint(10, 1000),
                'engagement_rate': random.uniform(0.01, 0.1),
                'has_link_in_bio': random.choice([True, False]),
                'recent_activity': random.randint(1, 30)  # days ago
            }
        
        # Real implementation would go here
        return None
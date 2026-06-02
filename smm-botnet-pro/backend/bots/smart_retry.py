"""
Smart Retry Handler - Implements retry logic with exponential backoff and fallback actions.
"""

import logging
import time
import random
from typing import Callable, Optional
from tenacity import (
    retry, stop_after_attempt, wait_exponential, 
    retry_if_exception_type, before_log, after_log
)
from django.conf import settings

logger = logging.getLogger(__name__)


class SmartRetryHandler:
    """Handles retry logic with fallback actions for failed operations."""
    
    def __init__(self):
        self.fallback_actions = [
            self._like_recent_post,
            self._comment_on_post,
            self._save_post,
            self._view_story
        ]
    
    def execute_with_retry(
        self, 
        operation: Callable[[], bool], 
        max_attempts: int = 3,
        use_fallback: bool = True
    ) -> bool:
        """
        Execute an operation with retry logic and fallback actions.
        
        Args:
            operation: Function that returns True on success, False on failure
            max_attempts: Maximum number of retry attempts
            use_fallback: Whether to try fallback actions after retries fail
            
        Returns:
            True if operation succeeded, False otherwise
        """
        # Try the main operation with retries
        try:
            result = self._retry_operation(operation, max_attempts)
            if result:
                return True
        except Exception as e:
            logger.warning(f"Main operation failed after retries: {e}")
        
        # If retries failed and fallback is enabled, try fallback actions
        if use_fallback:
            return self._try_fallback_actions()
        
        return False
    
    def _retry_operation(self, operation: Callable[[], bool], max_attempts: int) -> bool:
        """Execute operation with exponential backoff retry."""
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type(Exception),
            before=before_log(logger, logging.INFO),
            after=after_log(logger, logging.WARNING)
        )
        def _wrapped_operation():
            result = operation()
            if not result:
                # Raise an exception to trigger retry
                raise Exception("Operation returned False")
            return result
        
        try:
            return _wrapped_operation()
        except Exception as e:
            logger.error(f"Operation failed after {max_attempts} attempts: {e}")
            return False
    
    def _try_fallback_actions(self) -> bool:
        """Try fallback actions when main operation fails."""
        logger.info("Attempting fallback actions")
        
        # Shuffle fallback actions to add variety
        actions = self.fallback_actions.copy()
        random.shuffle(actions)
        
        for action in actions:
            try:
                logger.info(f"Trying fallback action: {action.__name__}")
                if action():
                    logger.info(f"Fallback action {action.__name__} succeeded")
                    return True
                else:
                    logger.info(f"Fallback action {action.__name__} failed")
            except Exception as e:
                logger.warning(f"Fallback action {action.__name__} raised exception: {e}")
            
            # Small delay between fallback attempts
            time.sleep(0.5)
        
        logger.info("All fallback actions failed")
        return False
    
    # Fallback action implementations (simulated)
    def _like_recent_post(self) -> bool:
        """Simulate liking a recent post."""
        if getattr(settings, 'SIMULATION_MODE', True):
            logger.info("SIMULATION: Liking recent post")
            time.sleep(random.uniform(0.5, 1.5))
            return random.random() > 0.1  # 90% success rate
        return False
    
    def _comment_on_post(self) -> bool:
        """Simulate commenting on a post."""
        if getattr(settings, 'SIMULATION_MODE', True):
            logger.info("SIMULATION: Commenting on post")
            time.sleep(random.uniform(1.0, 2.0))
            return random.random() > 0.2  # 80% success rate
        return False
    
    def _save_post(self) -> bool:
        """Simulate saving a post."""
        if getattr(settings, 'SIMULATION_MODE', True):
            logger.info("SIMULATION: Saving post")
            time.sleep(random.uniform(0.5, 1.0))
            return random.random() > 0.1  # 90% success rate
        return False
    
    def _view_story(self) -> bool:
        """Simulate viewing a story."""
        if getattr(settings, 'SIMULATION_MODE', True):
            logger.info("SIMULATION: Viewing story")
            time.sleep(random.uniform(0.5, 1.0))
            return random.random() > 0.05  # 95% success rate
        return False


# Global instance
retry_handler = SmartRetryHandler()
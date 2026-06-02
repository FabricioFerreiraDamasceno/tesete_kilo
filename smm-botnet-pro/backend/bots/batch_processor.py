"""
Batch Processor - Implements batch processing for efficient database operations.
"""

import logging
import threading
import time
from typing import List, Tuple, Dict
from django.db import transaction
from django.utils import timezone
from .models import BotAccount

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Processes database operations in batches for efficiency."""
    
    def __init__(self, batch_size: int = 50, flush_interval: float = 5.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._lock = threading.Lock()
        self._follow_actions = []  # List of (bot_id, target_user) tuples
        self._last_flush = time.time()
        self._flush_thread = None
        self._running = False
    
    def start(self):
        """Start the batch processor background thread."""
        if self._running:
            return
        
        self._running = True
        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._flush_thread.start()
        logger.info("Batch processor started")
    
    def stop(self):
        """Stop the batch processor and flush remaining items."""
        self._running = False
        if self._flush_thread:
            self._flush_thread.join(timeout=5.0)
        self.flush()
        logger.info("Batch processor stopped")
    
    def add_follow_action(self, bot_id: int, target_user: str):
        """Add a follow action to the batch."""
        with self._lock:
            self._follow_actions.append((bot_id, target_user))
            
            # Check if we should flush
            if len(self._follow_actions) >= self.batch_size:
                self.flush()
    
    def flush(self):
        """Flush all pending operations to the database."""
        with self._lock:
            if not self._follow_actions:
                return
            
            actions_to_process = self._follow_actions.copy()
            self._follow_actions.clear()
        
        if not actions_to_process:
            return
        
        logger.debug(f"Flushing {len(actions_to_process)} follow actions to database")
        
        try:
            with transaction.atomic():
                # Group actions by bot_id for efficient updates
                bot_action_counts: Dict[int, int] = {}
                for bot_id, _ in actions_to_process:
                    bot_action_counts[bot_id] = bot_action_counts.get(bot_id, 0) + 1
                
                # Update each bot's daily_follows count
                for bot_id, count in bot_action_counts.items():
                    BotAccount.objects.filter(id=bot_id).update(
                        daily_follows=models.F('daily_follows') + count
                    )
                
            logger.debug(f"Successfully flushed {len(actions_to_process)} follow actions")
        except Exception as e:
            logger.error(f"Error flushing batch: {e}")
            # Re-add failed actions to try again later
            with self._lock:
                self._follow_actions.extend(actions_to_process)
    
    def _flush_loop(self):
        """Background loop that periodically flushes the batch."""
        while self._running:
            time.sleep(0.1)  # Check frequently
            
            # Check if it's time to flush based on interval
            if time.time() - self._last_flush >= self.flush_interval:
                self.flush()
                self._last_flush = time.time()


# Global instance
batch_processor = BatchProcessor()

# Convenience functions
def add_follow_action(bot_id: int, target_user: str):
    """Add a follow action to the global batch processor."""
    batch_processor.add_follow_action(bot_id, target_user)

def start_batch_processor():
    """Start the global batch processor."""
    batch_processor.start()

def stop_batch_processor():
    """Stop the global batch processor."""
    batch_processor.stop()
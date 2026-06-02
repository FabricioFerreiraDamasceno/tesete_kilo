"""
Priority Queue Implementation for Order Processing.
Uses a heap to manage orders by priority score.
"""

import heapq
import logging
from typing import Any, Optional, Tuple
from django.db import models

logger = logging.getLogger(__name__)


class PriorityQueue:
    """A priority queue implementation using heapq."""
    
    def __init__(self):
        self._queue = []
        self._index = 0  # Used to maintain insertion order for equal priorities
    
    def push(self, item: Any, priority: float):
        """Add an item to the queue with a given priority."""
        # We negate priority because heapq is a min queue, but we want max priority first
        heapq.heappush(self._queue, (-priority, self._index, item))
        self._index += 1
        logger.debug(f"Pushed item with priority {priority}")
    
    def pop(self) -> Optional[Any]:
        """Remove and return the highest priority item."""
        if self.is_empty():
            return None
        
        priority, index, item = heapq.heappop(self._queue)
        logger.debug(f"Popped item with priority {-priority}")
        return item
    
    def peek(self) -> Optional[Any]:
        """Return the highest priority item without removing it."""
        if self.is_empty():
            return None
        
        return self._queue[0][2]  # Return the item (third element)
    
    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return len(self._queue) == 0
    
    def size(self) -> int:
        """Return the number of items in the queue."""
        return len(self._queue)
    
    def clear(self):
        """Remove all items from the queue."""
        self._queue.clear()
        self._index = 0
        logger.debug("Priority queue cleared")
    
    def rebalance(self):
        """Rebalance the queue (heapify)."""
        heapq.heapify(self._queue)
        logger.debug("Priority queue rebalanced")


class WeightedPriorityQueue(PriorityQueue):
    """Priority queue that supports weight adjustments."""
    
    def update_priority(self, item: Any, new_priority: float):
        """Update the priority of an existing item."""
        # Find the item and update its priority
        for i, (neg_priority, index, existing_item) in enumerate(self._queue):
            if existing_item == item:
                # Remove the old entry
                del self._queue[i]
                # Add the new entry
                self.push(item, new_priority)
                # Reheapify
                heapq.heapify(self._queue)
                logger.debug(f"Updated priority for item to {new_priority}")
                return
        logger.warning(f"Item not found in queue for priority update")


# Global instance for use across the application
order_priority_queue = PriorityQueue()
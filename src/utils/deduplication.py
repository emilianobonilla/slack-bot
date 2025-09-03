"""
Deduplication utilities to prevent duplicate message processing.
"""
import os
import json
import time
import logging
from typing import Set, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MessageDeduplicator:
    """
    In-memory message deduplicator to prevent duplicate processing.
    In production, this could be backed by Redis or another persistent store.
    """
    
    def __init__(self, ttl_seconds: int = 300):  # 5 minutes TTL
        """
        Initialize deduplicator.
        
        Args:
            ttl_seconds: Time to live for processed message IDs
        """
        self.processed_messages: Dict[str, float] = {}
        self.ttl_seconds = ttl_seconds
        
    def is_duplicate(self, message_id: str) -> bool:
        """
        Check if a message has already been processed.
        
        Args:
            message_id: Unique identifier for the message
            
        Returns:
            bool: True if duplicate, False if new
        """
        # Clean old entries
        self._cleanup_old_entries()
        
        # Check if message was already processed
        if message_id in self.processed_messages:
            logger.warning(f"Duplicate message detected: {message_id}")
            return True
        
        # Mark message as processed
        self.processed_messages[message_id] = time.time()
        logger.debug(f"Message marked as processed: {message_id}")
        return False
    
    def _cleanup_old_entries(self):
        """Remove entries older than TTL."""
        current_time = time.time()
        cutoff_time = current_time - self.ttl_seconds
        
        old_keys = [
            msg_id for msg_id, timestamp in self.processed_messages.items()
            if timestamp < cutoff_time
        ]
        
        for key in old_keys:
            del self.processed_messages[key]
        
        if old_keys:
            logger.debug(f"Cleaned up {len(old_keys)} old message entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get deduplicator statistics."""
        self._cleanup_old_entries()
        return {
            "active_messages": len(self.processed_messages),
            "ttl_seconds": self.ttl_seconds,
            "oldest_entry": min(self.processed_messages.values()) if self.processed_messages else None
        }


# Global deduplicator instance
message_deduplicator = MessageDeduplicator()


def generate_message_id(event_data: Dict[str, Any]) -> str:
    """
    Generate a unique message ID from event data.
    
    Args:
        event_data: Slack event data
        
    Returns:
        str: Unique message identifier
    """
    # Create unique ID from user, channel, timestamp, and text
    components = [
        event_data.get("user_id", ""),
        event_data.get("channel_id", ""), 
        event_data.get("timestamp", ""),
        event_data.get("text", "")[:100]  # First 100 chars of text
    ]
    
    # Create a deterministic hash
    import hashlib
    message_content = "|".join(str(c) for c in components)
    message_id = hashlib.md5(message_content.encode()).hexdigest()
    
    return message_id


def is_duplicate_message(event_data: Dict[str, Any]) -> bool:
    """
    Check if a message is a duplicate based on event data.
    
    Args:
        event_data: Slack event data
        
    Returns:
        bool: True if duplicate, False if new
    """
    message_id = generate_message_id(event_data)
    return message_deduplicator.is_duplicate(message_id)

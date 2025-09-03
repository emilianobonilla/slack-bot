"""
Early deduplication system that works at the request level.
"""
import time
import logging
from typing import Dict, Set

logger = logging.getLogger(__name__)

# Global deduplication state that persists across Azure Functions instances
_processed_events: Dict[str, float] = {}
_processing_events: Set[str] = set()  # Events currently being processed

def is_duplicate_or_processing(event_id: str, ttl_seconds: int = 300) -> bool:
    """
    Check if an event is duplicate or currently being processed.
    
    Args:
        event_id: Unique event identifier
        ttl_seconds: Time to live for processed events
    
    Returns:
        bool: True if duplicate or processing, False if new
    """
    current_time = time.time()
    
    # Clean old entries
    cutoff_time = current_time - ttl_seconds
    old_keys = [k for k, v in _processed_events.items() if v < cutoff_time]
    for key in old_keys:
        _processed_events.pop(key, None)
        _processing_events.discard(key)
    
    # Check if already processed
    if event_id in _processed_events:
        logger.warning(f"Event already processed: {event_id}")
        return True
    
    # Check if currently being processed
    if event_id in _processing_events:
        logger.warning(f"Event currently being processed: {event_id}")
        return True
    
    # Mark as being processed
    _processing_events.add(event_id)
    logger.info(f"Event marked as processing: {event_id}")
    return False

def mark_event_completed(event_id: str):
    """Mark event as completed processing."""
    _processing_events.discard(event_id)
    _processed_events[event_id] = time.time()
    logger.info(f"Event marked as completed: {event_id}")

def get_stats() -> Dict:
    """Get deduplication statistics."""
    return {
        "processed_count": len(_processed_events),
        "currently_processing": len(_processing_events),
        "processing_events": list(_processing_events),
        "recent_processed": list(_processed_events.keys())[-10:] if _processed_events else []
    }

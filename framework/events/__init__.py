"""
Event bus framework for agent-to-agent communication.

Uses PostgreSQL pg_notify + LISTEN/NOTIFY with polling fallback.
No separate message broker required.
"""

from .envelope import EventEnvelope
from .producer import EventProducer
from .consumer import EventConsumer, EventHandler
from .dead_letter import DeadLetterQueue

__all__ = [
    "EventEnvelope",
    "EventProducer",
    "EventConsumer",
    "EventHandler",
    "DeadLetterQueue",
]

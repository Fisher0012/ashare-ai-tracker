from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import time
import json

class EventType(Enum):
    ANOMALY_DETECTION = "anomaly_detection"

class EventSubtype(Enum):
    SENTIMENT_TURNING_UP = "sentiment_turning_up"
    SENTIMENT_TURNING_DOWN = "sentiment_turning_down"
    FLOW_REVERSAL = "flow_reversal"
    FLOW_WITHDRAWAL = "flow_withdrawal"
    THEME_EMERGENCE = "theme_emergence"
    THEME_EXHAUSTION = "theme_exhaustion"

class EventLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class Event:
    event_id: str
    timestamp: float
    type: EventType
    subtype: EventSubtype
    level: EventLevel
    data: Dict[str, Any]
    description: str

    def to_dict(self):
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "type": self.type.value,
            "subtype": self.subtype.value,
            "level": self.level.value,
            "data": self.data,
            "description": self.description
        }

class MarketStatus(Enum):
    RED = "red"      # Risk / Overheated
    YELLOW = "yellow" # Oscillating / Observing
    GREEN = "green"   # Safe / Positive

@dataclass
class MarketState:
    timestamp: float
    status: MarketStatus
    sentiment_score: float # 0-100
    main_driver: str
    summary: str

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "status": self.status.value,
            "sentiment_score": self.sentiment_score,
            "main_driver": self.main_driver,
            "summary": self.summary
        }

class NotificationFormat(Enum):
    FLASH = "flash" # 1 line
    CARD = "card"   # <= 3 lines
    ALERT = "alert" # Strong signal

@dataclass
class Notification:
    notification_id: str
    timestamp: float
    format: NotificationFormat
    title: str
    lines: List[str]
    related_events: List[str]

    def to_dict(self):
        return {
            "notification_id": self.notification_id,
            "timestamp": self.timestamp,
            "format": self.format.value,
            "title": self.title,
            "lines": self.lines,
            "related_events": self.related_events
        }

from typing import List, Dict, Set
import time
import uuid
from .models import Event, Notification, NotificationFormat, EventLevel, MarketState

class NotificationService:
    def __init__(self):
        self.sent_notifications: List[Notification] = []
        self.last_sent_time: Dict[str, float] = {} # Key: subtype, Value: timestamp

    def generate_notifications(self, events: List[Event], market_state: MarketState) -> List[Notification]:
        notifications = []
        
        # Simple Logic: 1 Event -> Flash, >1 Events -> Card, High Level -> Alert
        
        # Filter events to avoid spamming same subtype within 30 mins
        unique_events = []
        for event in events:
            last_time = self.last_sent_time.get(event.subtype.value, 0)
            if time.time() - last_time > 1800: # 30 mins throttle
                unique_events.append(event)
                self.last_sent_time[event.subtype.value] = time.time()
        
        if not unique_events:
            return []

        # Check for High Priority (Alert)
        high_priority_events = [e for e in unique_events if e.level == EventLevel.HIGH]
        if high_priority_events:
            lines = [e.description for e in high_priority_events[:3]]
            lines.append(f"Market Status: {market_state.status.value.upper()}")
            
            notif = Notification(
                notification_id=f"notif_{uuid.uuid4().hex[:8]}",
                timestamp=time.time(),
                format=NotificationFormat.ALERT,
                title="重要市场预警",
                lines=lines,
                related_events=[e.event_id for e in high_priority_events]
            )
            notifications.append(notif)
            return notifications # Return immediately for high priority

        # Check for Multiple Events (Card)
        if len(unique_events) >= 2:
            lines = [e.description for e in unique_events[:2]]
            lines.append(f"Sentiment Score: {market_state.sentiment_score}")
            
            notif = Notification(
                notification_id=f"notif_{uuid.uuid4().hex[:8]}",
                timestamp=time.time(),
                format=NotificationFormat.CARD,
                title="市场多维信号",
                lines=lines,
                related_events=[e.event_id for e in unique_events]
            )
            notifications.append(notif)
        
        # Single Event (Flash)
        elif len(unique_events) == 1:
            event = unique_events[0]
            notif = Notification(
                notification_id=f"notif_{uuid.uuid4().hex[:8]}",
                timestamp=time.time(),
                format=NotificationFormat.FLASH,
                title="市场快讯",
                lines=[event.description],
                related_events=[event.event_id]
            )
            notifications.append(notif)

        self.sent_notifications.extend(notifications)
        return notifications

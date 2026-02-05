from typing import List, Optional
import time
from .models import MarketState, MarketStatus, Event, EventSubtype

class StateManager:
    def __init__(self):
        self.current_state = MarketState(
            timestamp=time.time(),
            status=MarketStatus.YELLOW, # Default start
            sentiment_score=50.0,
            main_driver="Initialization",
            summary="System starting up..."
        )
        self.recent_events: List[Event] = []

    def update_state(self, new_events: List[Event]) -> MarketState:
        # Prune events older than 30 minutes
        cutoff_time = time.time() - 1800
        self.recent_events = [e for e in self.recent_events if e.timestamp > cutoff_time]
        self.recent_events.extend(new_events)

        # Basic logic to update sentiment score and status
        # This is a simplified heuristic for MVP
        
        score_change = 0
        for event in new_events:
            if event.subtype == EventSubtype.SENTIMENT_TURNING_UP:
                score_change += 10
            elif event.subtype == EventSubtype.FLOW_REVERSAL:
                score_change += 5
            elif event.subtype == EventSubtype.THEME_EMERGENCE:
                score_change += 5
            elif event.subtype == EventSubtype.SENTIMENT_TURNING_DOWN:
                score_change -= 10
            elif event.subtype == EventSubtype.FLOW_WITHDRAWAL:
                score_change -= 10
            elif event.subtype == EventSubtype.THEME_EXHAUSTION:
                score_change -= 5
        
        new_score = max(0, min(100, self.current_state.sentiment_score + score_change))
        
        # Determine Status Color
        if new_score >= 70:
            status = MarketStatus.GREEN
        elif new_score <= 30:
            status = MarketStatus.RED
        else:
            status = MarketStatus.YELLOW

        # Determine Main Driver (Last significant event)
        driver = self.current_state.main_driver
        summary = self.current_state.summary
        
        if new_events:
            last_event = new_events[-1]
            driver = last_event.description
            summary = f"Updated by {last_event.subtype.value}"

        self.current_state = MarketState(
            timestamp=time.time(),
            status=status,
            sentiment_score=new_score,
            main_driver=driver,
            summary=summary
        )
        
        return self.current_state

    def get_recent_events(self) -> List[Event]:
        return self.recent_events

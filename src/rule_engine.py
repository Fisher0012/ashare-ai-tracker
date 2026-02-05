from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import time
import uuid
from .models import Event, EventType, EventSubtype, EventLevel

class Rule(ABC):
    @abstractmethod
    def evaluate(self, current_data: Dict[str, Any], history_window: List[Dict[str, Any]]) -> Optional[Event]:
        pass

class RuleEngine:
    def __init__(self):
        self.rules: List[Rule] = []

    def add_rule(self, rule: Rule):
        self.rules.append(rule)

    def evaluate_all(self, current_data: Dict[str, Any], history_window: List[Dict[str, Any]]) -> List[Event]:
        events = []
        for rule in self.rules:
            event = rule.evaluate(current_data, history_window)
            if event:
                events.append(event)
        return events

# --- Concrete Rule Implementations ---

class SentimentTurningUpRule(Rule):
    def evaluate(self, current_data: Dict[str, Any], history_window: List[Dict[str, Any]]) -> Optional[Event]:
        # Logic: CurrentVolume > AvgVolume(30m) * 1.3 AND IndexChange > 0 AND LimitUpCount > Last(15m)
        
        # Simplified Mock Logic for MVP:
        # Check if 'volume' is 30% higher than average of last 30 points
        # Check if 'index_change' > 0
        
        if not history_window:
            return None

        volumes = [d.get('volume', 0) for d in history_window[-30:]]
        avg_vol = sum(volumes) / len(volumes) if volumes else 0
        
        curr_vol = current_data.get('volume', 0)
        index_change = current_data.get('index_change_pct', 0)
        
        if avg_vol > 0 and curr_vol > avg_vol * 1.3 and index_change > 0:
            return Event(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                timestamp=time.time(),
                type=EventType.ANOMALY_DETECTION,
                subtype=EventSubtype.SENTIMENT_TURNING_UP,
                level=EventLevel.MEDIUM,
                data={
                    "metric": "volume_spike",
                    "value": curr_vol,
                    "baseline": avg_vol,
                    "change_pct": (curr_vol - avg_vol) / avg_vol
                },
                description="Market sentiment turning up: Volume spike with index rise."
            )
        return None

class SentimentTurningDownRule(Rule):
    def evaluate(self, current_data: Dict[str, Any], history_window: List[Dict[str, Any]]) -> Optional[Event]:
        # Logic: IndexChange < 0 AND LimitDownCount > 3 AND BombRate > 30%
        
        index_change = current_data.get('index_change_pct', 0)
        limit_down = current_data.get('limit_down_count', 0)
        bomb_rate = current_data.get('bomb_rate', 0) # 0-100
        
        if index_change < 0 and limit_down > 3 and bomb_rate > 30:
             return Event(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                timestamp=time.time(),
                type=EventType.ANOMALY_DETECTION,
                subtype=EventSubtype.SENTIMENT_TURNING_DOWN,
                level=EventLevel.HIGH,
                data={
                    "metric": "sentiment_drop",
                    "limit_down": limit_down,
                    "bomb_rate": bomb_rate
                },
                description="Market sentiment turning down: Limit downs increasing."
            )
        return None

class FlowReversalRule(Rule):
    def evaluate(self, current_data: Dict[str, Any], history_window: List[Dict[str, Any]]) -> Optional[Event]:
        # Logic: NorthBoundNetFlow slope turns positive after being negative
        
        # Simplified: Check if current flow > 0 and previous flow < 0
        if not history_window:
            return None
            
        curr_flow = current_data.get('north_bound_flow', 0)
        prev_flow = history_window[-1].get('north_bound_flow', 0)
        
        if curr_flow > 0 and prev_flow < 0:
             return Event(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                timestamp=time.time(),
                type=EventType.ANOMALY_DETECTION,
                subtype=EventSubtype.FLOW_REVERSAL,
                level=EventLevel.MEDIUM,
                data={
                    "metric": "flow_reversal",
                    "current": curr_flow,
                    "previous": prev_flow
                },
                description="Capital flow reversal: Northbound funds turning positive."
            )
        return None

class FlowWithdrawalRule(Rule):
    def evaluate(self, current_data: Dict[str, Any], history_window: List[Dict[str, Any]]) -> Optional[Event]:
        # Logic: NorthBoundNetFlow rapid outflow (> 10M in 1 min for demo, or accumulated)
        
        curr_flow = current_data.get('north_bound_flow', 0)
        
        # Assume flow is net flow for the minute. If large negative.
        if curr_flow < -10000000: # -10 Million
             return Event(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                timestamp=time.time(),
                type=EventType.ANOMALY_DETECTION,
                subtype=EventSubtype.FLOW_WITHDRAWAL,
                level=EventLevel.HIGH,
                data={
                    "metric": "rapid_outflow",
                    "value": curr_flow
                },
                description="Significant capital withdrawal detected."
            )
        return None

class ThemeEmergenceRule(Rule):
    def evaluate(self, current_data: Dict[str, Any], history_window: List[Dict[str, Any]]) -> Optional[Event]:
        # Logic: SectorRank Top3 changes vs 15m ago
        
        curr_top_sector = current_data.get('top_sector', "")
        
        if not history_window:
            return None
            
        # Check 15 mins ago (approx 15 ticks)
        if len(history_window) >= 15:
            past_top_sector = history_window[-15].get('top_sector', "")
            if curr_top_sector != past_top_sector and curr_top_sector != "":
                 return Event(
                    event_id=f"evt_{uuid.uuid4().hex[:8]}",
                    timestamp=time.time(),
                    type=EventType.ANOMALY_DETECTION,
                    subtype=EventSubtype.THEME_EMERGENCE,
                    level=EventLevel.MEDIUM,
                    data={
                        "metric": "new_leader",
                        "sector": curr_top_sector,
                        "old_leader": past_top_sector
                    },
                    description=f"New market theme emerging: {curr_top_sector}."
                )
        return None

class ThemeExhaustionRule(Rule):
    def evaluate(self, current_data: Dict[str, Any], history_window: List[Dict[str, Any]]) -> Optional[Event]:
        # Logic: Leading sector drops
        
        curr_top_sector_change = current_data.get('top_sector_change_pct', 0)
        
        if curr_top_sector_change < -2.0: # Drops 2%
             return Event(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                timestamp=time.time(),
                type=EventType.ANOMALY_DETECTION,
                subtype=EventSubtype.THEME_EXHAUSTION,
                level=EventLevel.MEDIUM,
                data={
                    "metric": "sector_drop",
                    "value": curr_top_sector_change
                },
                description="Leading theme shows signs of exhaustion."
            )
        return None


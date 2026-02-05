import time
import random
from src.rule_engine import (
    RuleEngine, 
    SentimentTurningUpRule, 
    SentimentTurningDownRule,
    FlowReversalRule,
    FlowWithdrawalRule,
    ThemeEmergenceRule,
    ThemeExhaustionRule
)
from src.state_manager import StateManager
from src.notification_service import NotificationService

def main():
    # 1. Initialize Components
    rule_engine = RuleEngine()
    rule_engine.add_rule(SentimentTurningUpRule())
    rule_engine.add_rule(SentimentTurningDownRule())
    rule_engine.add_rule(FlowReversalRule())
    rule_engine.add_rule(FlowWithdrawalRule())
    rule_engine.add_rule(ThemeEmergenceRule())
    rule_engine.add_rule(ThemeExhaustionRule())

    state_manager = StateManager()
    notification_service = NotificationService()

    print("System Initialized. Starting Simulation...")
    print("-" * 50)

    # 2. Simulate Data Stream
    # We will simulate a sequence of time steps
    
    history_window = []

    # Scenario 1: Normal Market (Baseline) - Steps 0-29
    for i in range(30):
        data_point = {
            "timestamp": time.time(),
            "volume": 1000000 + random.randint(-100000, 100000),
            "index_change_pct": 0.0,
            "north_bound_flow": 0,
            "limit_down_count": 0,
            "bomb_rate": 5,
            "top_sector": "Banking"
        }
        history_window.append(data_point)

    # Scenario 2: Sentiment Turning Up (Step 30)
    print("\n[Simulating Time Step: Sentiment Turning Up]")
    current_data = {
        "timestamp": time.time(),
        "volume": 1400000, # 40% higher than avg
        "index_change_pct": 0.5,
        "north_bound_flow": 500000,
        "limit_down_count": 0,
        "bomb_rate": 5,
        "top_sector": "Banking"
    }
    
    process_step(current_data, history_window, rule_engine, state_manager, notification_service)
    history_window.append(current_data)
    
    # Scenario 3: Flow Reversal (Step 31)
    # Need to set previous flow to negative to trigger reversal
    history_window[-1]["north_bound_flow"] = -200000 
    
    print("\n[Simulating Time Step: Flow Reversal]")
    current_data = {
        "timestamp": time.time(),
        "volume": 1100000,
        "index_change_pct": 0.2,
        "north_bound_flow": 300000, # Positive now
        "limit_down_count": 0,
        "bomb_rate": 5,
        "top_sector": "Banking"
    }
    
    process_step(current_data, history_window, rule_engine, state_manager, notification_service)
    history_window.append(current_data)

    # Scenario 4: Multiple Events (Step 32)
    print("\n[Simulating Time Step: Multiple Events (Theme + Sentiment Drop)]")
    current_data = {
        "timestamp": time.time(),
        "volume": 1000000,
        "index_change_pct": -0.5,
        "north_bound_flow": 0,
        "limit_down_count": 4, # Trigger Sentiment Down
        "bomb_rate": 35, # Trigger Sentiment Down
        "top_sector": "Semiconductor", # Changed from Banking -> Theme Emergence
        "top_sector_change_pct": 1.0
    }
    
    # Manually adjust history to ensure Theme Emergence triggers (needs old leader 15 steps ago)
    # History has Banking as top sector
    
    process_step(current_data, history_window, rule_engine, state_manager, notification_service)
    history_window.append(current_data)


def process_step(current_data, history_window, rule_engine, state_manager, notification_service):
    # 1. Evaluate Rules
    events = rule_engine.evaluate_all(current_data, history_window)
    
    if events:
        print(f"-> Generated {len(events)} Events:")
        for e in events:
            print(f"   - [{e.subtype.value}] {e.description}")
    else:
        print("-> No Events Generated")

    # 2. Update State
    new_state = state_manager.update_state(events)
    print(f"-> Market State: {new_state.status.value.upper()} (Score: {new_state.sentiment_score})")

    # 3. Generate Notifications
    notifications = notification_service.generate_notifications(events, new_state)
    
    if notifications:
        print(f"-> USER NOTIFICATION ({notifications[0].format.value}):")
        print(f"   Title: {notifications[0].title}")
        for line in notifications[0].lines:
            print(f"   Line: {line}")
    else:
        print("-> No Notification (Throttled or Empty)")

if __name__ == "__main__":
    main()

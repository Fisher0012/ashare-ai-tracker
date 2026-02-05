# A-Share AI Intraday Tracker (MVP)

This is the MVP implementation of the AI Intraday Tracker for the A-Share market. It monitors market data streams, detects anomalies using a rule engine, and generates user-friendly notifications.

## Project Structure

- `src/models.py`: Defines core data structures (`Event`, `Notification`, `MarketState`).
- `src/rule_engine.py`: Contains the logic for detecting anomalies (Sentiment, Flow, Theme).
- `src/state_manager.py`: Manages the global market state (Red/Yellow/Green) and aggregates events.
- `src/notification_service.py`: Handles notification formatting, throttling, and prioritization.
- `main.py`: A simulation driver that demonstrates the system flow with mock data.
- `DESIGN.md`: Detailed system design document.

## Features

- **6 Anomaly Detection Rules**:
    1.  `sentiment_turning_up`: Volume spike + Index rise.
    2.  `sentiment_turning_down`: Index drop + Limit downs + Bomb rate.
    3.  `flow_reversal`: Northbound funds turning positive.
    4.  `flow_withdrawal`: Rapid capital outflow.
    5.  `theme_emergence`: New sector entering top ranks.
    6.  `theme_exhaustion`: Leading sector dropping.
- **Unified JSON Output**: Standardized formats for internal events and external notifications.
- **Notification Throttling**: Prevents spamming the same signal within 30 minutes.

## How to Run

1.  Ensure you have Python 3 installed.
2.  Run the simulation script:

```bash
python3 main.py
```

## Next Steps

- Integrate real-time data sources (e.g., Tushare, Sina Finance).
- Refine rule thresholds based on backtesting.
- Develop the frontend UI to render the JSON notifications.

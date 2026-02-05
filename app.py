import streamlit as st
import time
import pandas as pd
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
from src.data_provider import MockDataProvider, AkShareDataProvider
from src.models import MarketStatus, NotificationFormat

# Page Config
st.set_page_config(
    page_title="A-Share AI Tracker",
    page_icon="📈",
    layout="wide"
)

# --- CSS Styling ---
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    .status-card {
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        color: white;
        font-weight: bold;
        font-size: 24px;
    }
    .status-red { background-color: #ff4b4b; }
    .status-yellow { background-color: #ffa500; }
    .status-green { background-color: #4caf50; }
    
    .notif-card {
        border-left: 5px solid #2196f3;
        background-color: #f8f9fa;
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 5px;
    }
    .notif-alert {
        border-left: 5px solid #ff4b4b;
        background-color: #fff0f0;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialization (Session State) ---
if 'initialized' not in st.session_state:
    st.session_state.rule_engine = RuleEngine()
    st.session_state.rule_engine.add_rule(SentimentTurningUpRule())
    st.session_state.rule_engine.add_rule(SentimentTurningDownRule())
    st.session_state.rule_engine.add_rule(FlowReversalRule())
    st.session_state.rule_engine.add_rule(FlowWithdrawalRule())
    st.session_state.rule_engine.add_rule(ThemeEmergenceRule())
    st.session_state.rule_engine.add_rule(ThemeExhaustionRule())
    
    st.session_state.state_manager = StateManager()
    st.session_state.notification_service = NotificationService()
    st.session_state.data_provider = MockDataProvider()
    
    st.session_state.history_window = []
    st.session_state.notifications_log = []
    st.session_state.market_data_log = []
    
    st.session_state.initialized = True

# --- Main Logic Function ---
def update_system():
    # 1. Get Data
    data = st.session_state.data_provider.get_latest_market_snapshot()
    st.session_state.history_window.append(data)
    
    # Keep window manageable
    if len(st.session_state.history_window) > 100:
        st.session_state.history_window.pop(0)

    # Log for charts
    st.session_state.market_data_log.append({
        "time": time.strftime("%H:%M:%S", time.localtime(data["timestamp"])),
        "index_change": data["index_change_pct"],
        "volume": data["volume"]
    })

    # 2. Rule Engine
    events = st.session_state.rule_engine.evaluate_all(
        data, st.session_state.history_window[:-1] # Exclude current for history comparison
    )

    # 3. State Manager
    new_state = st.session_state.state_manager.update_state(events)
    
    # 4. Notification Service
    notifs = st.session_state.notification_service.generate_notifications(events, new_state)
    
    # Prepend new notifications to log
    for n in notifs:
        st.session_state.notifications_log.insert(0, n)

# --- UI Layout ---

st.title("A-Share AI Intraday Tracker (MVP)")

# Sidebar controls
with st.sidebar:
    st.header("Settings")
    
    # Data Source Selection
    data_source = st.radio(
        "Data Source",
        ["Mock (Simulation)", "Real (AkShare)"],
        index=0
    )
    
    # Handle Data Source Switch
    if data_source == "Real (AkShare)" and isinstance(st.session_state.data_provider, MockDataProvider):
        st.session_state.data_provider = AkShareDataProvider()
        st.toast("Switched to Real Data Source")
    elif data_source == "Mock (Simulation)" and not isinstance(st.session_state.data_provider, MockDataProvider):
        st.session_state.data_provider = MockDataProvider()
        st.toast("Switched to Mock Data Source")

    st.divider()
    st.header("Control")
    
    if st.button("Step Forward / Refresh"):
        update_system()
    
    # Auto run interval depends on source
    interval = 2 if data_source == "Mock (Simulation)" else 60
    auto_run = st.checkbox(f"Auto Run ({interval}s Interval)")

if auto_run:
    time.sleep(interval)
    update_system()
    st.rerun()

# Get current state
current_state = st.session_state.state_manager.current_state

# Top Row: Market Status
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.subheader("Market Status")
    status_color = current_state.status.value
    st.markdown(f"""
        <div class="status-card status-{status_color}">
            {status_color.upper()}
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.subheader("Core Driver")
    st.info(f"**{current_state.main_driver}**")
    st.caption(current_state.summary)

with col3:
    st.metric("Sentiment Score", f"{current_state.sentiment_score:.0f}", delta=None)

st.divider()

# Middle Row: Charts & Notifications
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("Market Trend (Index %)")
    if st.session_state.market_data_log:
        df = pd.DataFrame(st.session_state.market_data_log)
        st.line_chart(df.set_index("time")["index_change"])
    else:
        st.info("Waiting for data...")

with c2:
    st.subheader("Live Signals")
    if not st.session_state.notifications_log:
        st.write("No signals yet.")
    
    for notif in st.session_state.notifications_log[:5]: # Show last 5
        css_class = "notif-alert" if notif.format == NotificationFormat.ALERT else "notif-card"
        
        with st.container():
            st.markdown(f"""
            <div class="{css_class}">
                <strong>[{notif.format.value.upper()}] {notif.title}</strong><br>
                <small>{time.strftime('%H:%M:%S', time.localtime(notif.timestamp))}</small>
            </div>
            """, unsafe_allow_html=True)
            for line in notif.lines:
                st.write(f"- {line}")

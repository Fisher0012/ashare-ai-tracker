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
    page_title="A股 AI 盘中追踪",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed" # Better for mobile
)

# --- CSS Styling (Mobile Optimized) ---
st.markdown("""
<style>
    /* Global Font */
    body {
        font-family: "Source Sans Pro", sans-serif;
    }
    
    /* Mobile-first layout adjustments */
    .stMetric {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .status-card {
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        color: white;
        font-weight: bold;
        font-size: 20px;
        margin-bottom: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.15);
    }
    .status-red { background-color: #ff4b4b; background-image: linear-gradient(135deg, #ff4b4b 0%, #ff0000 100%); }
    .status-yellow { background-color: #ffa500; background-image: linear-gradient(135deg, #ffa500 0%, #ff8c00 100%); }
    .status-green { background-color: #4caf50; background-image: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%); }
    
    .notif-card {
        border-left: 5px solid #2196f3;
        background-color: white;
        padding: 12px;
        margin-bottom: 12px;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        font-size: 14px;
    }
    .notif-alert {
        border-left: 5px solid #ff4b4b;
        background-color: #fff5f5;
        padding: 12px;
        margin-bottom: 12px;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        font-size: 14px;
    }
    
    /* Headers */
    h1 { font-size: 1.8rem !important; margin-bottom: 1rem !important; }
    h3 { font-size: 1.2rem !important; margin-top: 0.5rem !important; }
    
    /* Hide footer */
    footer {visibility: hidden;}
    
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
    
    # Try to fetch Real Data first for initialization
    init_data = None
    try:
        real_provider = AkShareDataProvider()
        init_data = real_provider.get_latest_market_snapshot()
        # Check if data is valid (not empty placeholder)
        if init_data["volume"] == 0 and not init_data["top_sector_constituents"]:
            init_data = None # Treat as fail if empty
    except:
        pass
        
    # Fallback to Mock if Real failed
    if not init_data:
        mock_provider = MockDataProvider()
        init_data = mock_provider.get_latest_market_snapshot()
        
    st.session_state.history_window.append(init_data)
    
    st.session_state.market_data_log.append({
        "time": time.strftime("%H:%M:%S", time.localtime(init_data["timestamp"])),
        "index_change": init_data["index_change_pct"],
        "volume": init_data["volume"]
    })

# --- Main Logic Function ---
def update_system():
    """Fetch latest data, evaluate rules, and update system state."""
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

st.title("A股 AI 盘中追踪")

# Sidebar controls
with st.sidebar:
    st.header("系统设置")
    
    # Data Source Selection
    data_source = st.radio(
        "数据源选择",
        ["模拟数据 (Mock)", "实盘数据 (AkShare)"],
        index=0
    )
    
    # Handle Data Source Switch
    if data_source == "实盘数据 (AkShare)" and isinstance(st.session_state.data_provider, MockDataProvider):
        st.session_state.data_provider = AkShareDataProvider()
        st.toast("已切换至实盘数据源")
    elif data_source == "模拟数据 (Mock)" and not isinstance(st.session_state.data_provider, MockDataProvider):
        st.session_state.data_provider = MockDataProvider()
        st.toast("已切换至模拟数据源")

    st.divider()
    st.header("运行控制")
    
    if st.button("手动刷新 / 单步执行"):
        update_system()
    
    # Auto run interval depends on source
    interval = 2 if data_source == "模拟数据 (Mock)" else 60
    auto_run = st.checkbox(f"自动运行 (每 {interval} 秒)")

if auto_run:
    time.sleep(interval)
    update_system()
    st.rerun()

# Get current state
current_state = st.session_state.state_manager.current_state

# --- Dashboard Layout (Mobile Friendly) ---

# Top Row: Market Status
col1, col2, col3 = st.columns([1, 1.5, 1])

with col1:
    status_map = {
        "red": "高风险 / 过热",
        "yellow": "震荡 / 观察",
        "green": "积极 / 安全"
    }
    status_text = status_map.get(current_state.status.value, "未知")
    status_color = current_state.status.value
    
    st.markdown(f"""
        <div style="font-size:12px; color:gray; margin-bottom:5px;">市场状态</div>
        <div class="status-card status-{status_color}">
            {status_text}
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.metric("核心驱动因素", current_state.main_driver, help="导致当前市场状态变化的主要原因")

with col3:
    st.metric("情绪评分 (0-100)", f"{current_state.sentiment_score:.0f}")

st.divider()

# Middle Row: Charts & Notifications
# On mobile, these will stack automatically
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("大盘分时趋势")
    if st.session_state.market_data_log:
        df = pd.DataFrame(st.session_state.market_data_log)
        # Simple line chart
        st.line_chart(
            df.set_index("time")["index_change"],
            height=250,
            use_container_width=True
        )
    else:
        st.info("等待数据接入中...")

with c2:
    st.subheader("实时信号流")
    if not st.session_state.notifications_log:
        st.caption("暂无异常信号")
    
    for notif in st.session_state.notifications_log[:10]: # Show last 10
        css_class = "notif-alert" if notif.format == NotificationFormat.ALERT else "notif-card"
        
        # Translate format types for UI
        type_map = {
            "flash": "快讯",
            "card": "信号",
            "alert": "预警"
        }
        type_text = type_map.get(notif.format.value, "消息")
        
        with st.container():
            st.markdown(f"""
            <div class="{css_class}">
                <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                    <span style="font-weight:bold; color:#333;">[{type_text}] {notif.title}</span>
                    <span style="font-size:0.8em; color:#666;">{time.strftime('%H:%M:%S', time.localtime(notif.timestamp))}</span>
                </div>
                <div style="font-size:0.9em; color:#444;">
            """, unsafe_allow_html=True)
            
            for line in notif.lines:
                st.markdown(f"- {line}")
            
            st.markdown("</div></div>", unsafe_allow_html=True)

st.divider()

# Bottom Row: Tabs for Ladder, LHB, Notices
tab1, tab2, tab3 = st.tabs(["� 涨停梯队", "�� 龙虎榜", "📢 突发公告"])

data_snapshot = st.session_state.history_window[-1] if st.session_state.history_window else {}

with tab1:
    ladder = data_snapshot.get("limit_up_ladder", {})
    if ladder:
        cols = st.columns(4)
        with cols[0]:
            st.markdown("##### 🏆 高标 (4板+)")
            for stock in ladder.get("4板+", []):
                st.markdown(f"<span style='color:red; font-weight:bold;'>{stock}</span>", unsafe_allow_html=True)
        with cols[1]:
            st.markdown("##### 🥈 中位 (3板)")
            for stock in ladder.get("3板", []):
                st.markdown(f"{stock}")
        with cols[2]:
            st.markdown("##### 🥉 晋级 (2板)")
            for stock in ladder.get("2板", []):
                st.markdown(f"{stock}")
        with cols[3]:
            st.markdown("##### 🌱 首板挖掘")
            first_board = ladder.get("1板", [])
            st.caption(f"共 {len(first_board)} 只，展示前5:")
            for stock in first_board[:5]:
                st.markdown(f"{stock}")
    else:
        st.info("暂无连板数据")

with tab2:
    lhb_list = data_snapshot.get("dragon_tiger_list", [])
    if lhb_list:
        for item in lhb_list:
            st.success(f"**{item['name']}**: {item['reason']} (净买入 {item['net_buy']/10000:.0f} 万)")
    else:
        st.caption("暂无机构大额净买入数据")

with tab3:
    notices = data_snapshot.get("latest_notices", [])
    if notices:
        for note in notices:
            st.markdown(f"**[{note['time']}]** {note['title']}")
    else:
        st.caption("暂无突发利好公告")

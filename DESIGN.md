# A股 AI 盘中追踪工具 (MVP) 设计方案

## 1. 系统架构设计

系统采用流式处理架构，主要包含以下模块：

```mermaid
graph TD
    A[数据源 (Data Sources)] -->|实时流| B(数据接入层 (Ingestion))
    B --> C{规则引擎 (Rule Engine)}
    C -->|生成 Event| D[状态管理器 (State Manager)]
    D -->|更新 MarketState| E[通知服务 (Notification Service)]
    D -->|聚合 Event| E
    E -->|生成 Notification| F[用户界面 (UI/Output)]
```

### 模块职责
- **数据接入层**: 负责对接行情 API (分钟级 K 线、分时成交)、新闻源，进行数据清洗和标准化。
- **规则引擎**: 核心逻辑层，实时计算指标，与历史窗口（15-30分钟）对比，识别异常并生成 `Event`。
- **状态管理器**: 维护当前市场状态（红/黄/绿），缓存近期的 Events 用于去重和聚合。
- **通知服务**: 将 Events 转化为用户可读的 `Notification`，执行节流（Throttling）和去重策略。

## 2. 核心数据流

1.  **输入**:
    *   `Tick/1min Bar` (指数、个股、ETF)
    *   `News Stream` (快讯)
2.  **处理**:
    *   计算衍生指标：炸板率、资金流向净额、板块涨幅排名。
    *   规则匹配：例如 "当前成交额 > 过去30分钟均值 * 1.5" AND "指数涨幅 > 0.5%" -> 触发 `sentiment_turning_up`。
3.  **中间产物 (Event)**:
    *   产生一个 `Event` 对象，包含类型、时间戳、原始数据快照。
4.  **输出 (Notification)**:
    *   根据 Event 优先级和当前积累的 Event 列表，生成“一句话快讯”或“信号卡片”。

## 3. 统一数据结构 (JSON Schema)

### 3.1 Event (内部原始事件)

```json
{
  "event_id": "evt_123456789",
  "timestamp": 1717641600,
  "type": "anomaly_detection",
  "subtype": "sentiment_turning_up",
  "level": "medium",  // low, medium, high
  "data": {
    "index": "sh000001",
    "metric": "volume_spike",
    "value": 1500000000,
    "baseline_30m": 1000000000,
    "change_pct": 0.5
  },
  "description": "上证指数放量上涨，偏离基准50%"
}
```

### 3.2 MarketState (市场状态灯)

```json
{
  "timestamp": 1717641600,
  "status": "red", // red (风险/过热), yellow (震荡/观察), green (安全/积极)
  "sentiment_score": 75, // 0-100
  "main_driver": "北向资金大幅流入",
  "summary": "市场情绪转强，资金共识度提升"
}
```

### 3.3 Notification (面向用户输出)

```json
{
  "notification_id": "notif_987654321",
  "timestamp": 1717641605,
  "format": "card", // flash (一句话), card (卡片), alert (强弹窗)
  "title": "资金回流预警",
  "lines": [
    "北向资金 10:30 后快速回流 15 亿",
    "半导体 ETF 同步放量，溢价率扩大",
    "情绪指标：转强"
  ],
  "related_events": ["evt_123456789", "evt_123456790"]
}
```

## 4. 规则引擎实现思路 (MVP)

使用滑动窗口（Sliding Window）进行异常检测。

### 异常类型与判断逻辑

| Subtype | 核心逻辑 (伪代码) | 触发阈值示例 |
| :--- | :--- | :--- |
| **sentiment_turning_up** | `CurrentVolume > AvgVolume(30m) * 1.3` AND `IndexChange > 0` AND `LimitUpCount > Last(15m)` | 放量上涨，涨停家数增加 |
| **sentiment_turning_down** | `IndexChange < 0` AND `LimitDownCount > 3` AND `BombRate > 30%` | 指数下跌，炸板率飙升 |
| **flow_reversal** | `NorthBoundNetFlow` 斜率由负转正 (连续3分钟) OR `ETF_Volume > Avg(30m) * 2` | 北向V型反转 或 ETF巨量 |
| **flow_withdrawal** | `NorthBoundNetFlow` 快速流出 (>10亿/10min) | 外资快速撤离 |
| **theme_emergence** | `SectorRank` 此时 Top3 != 15分钟前 Top3 AND `SectorVolume` 放量 | 新板块挤入涨幅榜前列 |
| **theme_exhaustion** | 领涨板块龙头股 `Price` 跌破 `VWAP` AND `SectorIndex` 滞涨 | 龙头跳水，板块跟跌 |

## 5. 示例输出

### 场景 1：单一异常 (一句话快讯)
> **[快讯]** 10:15 半导体板块异动，成交额较前30分钟均值放大 50%。

### 场景 2：多指标共振 (信号卡片)
> **[信号] 资金回流拐点**
> 北向资金近 10 分钟净流入 20 亿，斜率陡峭。
> 创业板指同步拉升 0.8%，量能配合放大。
> 市场状态：由 🟡 转 🟢。

### 场景 3：结构性拐点 (强信号弹窗)
> **[重要] 情绪显著退潮**
> 高位连板股出现批量炸板，炸板率突破 40%。
> 市场量能萎缩，全市场下跌家数超 3500 家。
> 建议关注风控，暂缓开仓。

---
**下一步计划**:
确认此设计方案后，将开始搭建项目骨架，实现 `MarketState` 类和基础的 `RuleEngine` 框架。

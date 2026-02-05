from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import time
import random

# Try to import akshare, handle if not installed
try:
    import akshare as ak
    import pandas as pd
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False

class DataProvider(ABC):
    """
    Abstract Base Class for Data Provision.
    Allows switching between Mock data and Real data seamlessly.
    """
    @abstractmethod
    def get_latest_market_snapshot(self) -> Dict[str, Any]:
        """
        Returns a dictionary containing:
        - timestamp
        - volume
        - index_change_pct
        - north_bound_flow
        - limit_down_count
        - bomb_rate
        - top_sector
        - top_sector_change_pct
        - top_sector_constituents (List[Dict]: symbol, name, change_pct)
        - dragon_tiger_list (List[Dict]: name, reason, net_buy)
        - latest_notices (List[Dict]: title, time, url)
        - limit_up_ladder (Dict[str, List[str]]): { "4板+": [], "3板": [], "2板": [] } [New]
        """
        pass

class MockDataProvider(DataProvider):
    """
    Generates random market data for testing/simulation.
    """
    def __init__(self):
        self.base_volume = 1000000
        self.trend = 0 # -1 to 1
        self.sectors = {
            "Semiconductor": ["SMIC", "NAURA", "Cambricon"],
            "Banking": ["ICBC", "CCB", "CMB"],
            "Liquor": ["Kweichow Moutai", "Wuliangye", "Shanxi Fenjiu"],
            "New Energy": ["CATL", "BYD", "Sungrow"],
            "Medicine": ["Hengrui", "Mindray", "WuXi AppTec"]
        }
        
    def get_latest_market_snapshot(self) -> Dict[str, Any]:
        # Simulate some random walk
        self.trend += random.uniform(-0.1, 0.1)
        self.trend = max(-1, min(1, self.trend))
        
        sector_name = random.choice(list(self.sectors.keys()))
        sector_change = self.trend * 2 + random.uniform(-0.5, 0.5)
        
        # Mock constituents
        constituents = []
        for stock in self.sectors[sector_name]:
            constituents.append({
                "name": stock,
                "symbol": f"600{random.randint(100, 999)}",
                "change_pct": sector_change + random.uniform(0, 3)
            })
        constituents.sort(key=lambda x: x['change_pct'], reverse=True)
        
        # Mock Dragon Tiger
        dragon_list = []
        if random.random() > 0.7:
            dragon_list.append({
                "name": "Mock Stock A",
                "reason": "Day Limit Up",
                "net_buy": 50000000
            })

        # Mock Notices
        notices = []
        if random.random() > 0.8:
            notices.append({
                "title": f"Mock Company {random.randint(1,100)} Annual Report Pre-increase",
                "time": "10:30",
                "url": "#"
            })

        # Mock Limit Up Ladder
        ladder = {
            "4板+": [f"High Stock {i}" for i in range(random.randint(0, 2))],
            "3板": [f"Mid Stock {i}" for i in range(random.randint(0, 3))],
            "2板": [f"Low Stock {i}" for i in range(random.randint(1, 5))],
            "1板": [f"First Stock {i}" for i in range(random.randint(5, 10))]
        }

        return {
            "timestamp": time.time(),
            "volume": self.base_volume * (1 + random.uniform(-0.2, 0.5)),
            "index_change_pct": self.trend + random.uniform(-0.2, 0.2),
            "north_bound_flow": random.uniform(-10000000, 10000000) + (self.trend * 5000000),
            "limit_down_count": int(max(0, 5 - self.trend * 5 + random.randint(-1, 2))),
            "bomb_rate": max(0, min(100, 20 - self.trend * 10 + random.uniform(-5, 5))),
            "top_sector": sector_name,
            "top_sector_change_pct": sector_change,
            "top_sector_constituents": constituents,
            "dragon_tiger_list": dragon_list,
            "latest_notices": notices,
            "limit_up_ladder": ladder
        }

class AkShareDataProvider(DataProvider):
    """
    Fetches real-time data using AkShare.
    """
    def __init__(self):
        if not AKSHARE_AVAILABLE:
            raise ImportError("AkShare is not installed. Please run 'pip install akshare pandas'.")
            
    def get_latest_market_snapshot(self) -> Dict[str, Any]:
        try:
            # 1. Get Index Spot Data (Shanghai Composite - sh000001)
            df_index = ak.stock_zh_index_spot()
            sh_index = df_index[df_index['代码'] == 'sh000001'].iloc[0]
            
            volume = float(sh_index['成交额']) if '成交额' in sh_index else 0
            index_change = float(sh_index['涨跌幅']) if '涨跌幅' in sh_index else 0.0

            # 2. Get Top Sector (Industry Board)
            df_sector = ak.stock_board_industry_name_em()
            df_sector = df_sector.sort_values(by='涨跌幅', ascending=False)
            top_sector_row = df_sector.iloc[0]
            top_sector_name = top_sector_row['板块名称']
            top_sector_change = float(top_sector_row['涨跌幅'])
            
            # 3. Get Top Constituents for the Top Sector
            top_sector_constituents = []
            try:
                df_cons = ak.stock_board_industry_cons_em(symbol=top_sector_name)
                df_cons = df_cons.sort_values(by='涨跌幅', ascending=False)
                for _, row in df_cons.head(3).iterrows():
                    top_sector_constituents.append({
                        "name": row['名称'],
                        "symbol": row['代码'],
                        "change_pct": float(row['涨跌幅'])
                    })
            except Exception as e:
                print(f"Error fetching constituents for {top_sector_name}: {e}")

            # 4. Limit Up Count (Optional)
            limit_down_count = 0 
            bomb_rate = 0
            
            # 5. Dragon Tiger List (Daily)
            # Use 'stock_lhb_jgzz_sina' for institutional seats
            dragon_tiger_list = []
            try:
                # This fetches latest available LHB data
                df_lhb = ak.stock_lhb_jgzz_sina(date=time.strftime("%Y%m%d"))
                # Filter for Net Buy > 10M
                if not df_lhb.empty:
                    # Rename columns to match schema if needed, but akshare output varies
                    # Assuming columns like '股票名称', '净买入额'
                    for _, row in df_lhb.head(3).iterrows():
                        net_buy = float(row.get('净买入额', 0))
                        if net_buy > 10000000:
                            dragon_tiger_list.append({
                                "name": row.get('股票名称', 'Unknown'),
                                "reason": "Institutional Net Buy",
                                "net_buy": net_buy
                            })
            except:
                pass # Fail silently for LHB as it might be empty intraday
            
            # 6. Notices / News
            # stock_tease_ram(symbol="上证指数") is not ideal
            # Use stock_info_global_cls for fast news
            latest_notices = []
            try:
                # Fetch global news from Cailian Press (CLS)
                df_news = ak.stock_info_global_cls(symbol="A股24小时电报")
                # Filter for key words
                keywords = ["增长", "中标", "回购", "利好", "涨停"]
                for _, row in df_news.head(5).iterrows():
                    content = row['content']
                    title = row['title']
                    if any(k in content for k in keywords) or any(k in title for k in keywords):
                        latest_notices.append({
                            "title": title if title else content[:30] + "...",
                            "time": row['publish_time'],
                            "url": "#"
                        })
            except:
                pass

            # 7. Limit Up Ladder (Real-time)
            # stock_zt_pool_em(date="20240601")
            limit_up_ladder = {"4板+": [], "3板": [], "2板": [], "1板": []}
            try:
                date_str = time.strftime("%Y%m%d")
                # This API might return empty if not trading time or early morning
                df_zt = ak.stock_zt_pool_em(date=date_str)
                if not df_zt.empty:
                    # Column usually: '名称', '连板数'
                    for _, row in df_zt.iterrows():
                        name = row['名称']
                        lb_count = int(row['连板数'])
                        
                        if lb_count >= 4:
                            limit_up_ladder["4板+"].append(f"{name}({lb_count})")
                        elif lb_count == 3:
                            limit_up_ladder["3板"].append(name)
                        elif lb_count == 2:
                            limit_up_ladder["2板"].append(name)
                        else:
                            # Too many 1 ban, just count or take first few
                            if len(limit_up_ladder["1板"]) < 5:
                                limit_up_ladder["1板"].append(name)
            except:
                pass # Fail silently

            return {
                "timestamp": time.time(),
                "volume": volume,
                "index_change_pct": index_change,
                "north_bound_flow": 0, # Placeholder
                "limit_down_count": limit_down_count, 
                "bomb_rate": bomb_rate,
                "top_sector": top_sector_name,
                "top_sector_change_pct": top_sector_change,
                "top_sector_constituents": top_sector_constituents,
                "dragon_tiger_list": dragon_tiger_list,
                "latest_notices": latest_notices,
                "limit_up_ladder": limit_up_ladder
            }
        except Exception as e:
            print(f"Error fetching AkShare data: {e}")
            # Fallback to empty safe data
            return {
                "timestamp": time.time(),
                "volume": 0,
                "index_change_pct": 0,
                "north_bound_flow": 0,
                "limit_down_count": 0,
                "bomb_rate": 0,
                "top_sector": "Error",
                "top_sector_change_pct": 0,
                "top_sector_constituents": [],
                "dragon_tiger_list": [],
                "latest_notices": [],
                "limit_up_ladder": {"4板+": [], "3板": [], "2板": [], "1板": []}
            }

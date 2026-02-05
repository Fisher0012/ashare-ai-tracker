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
        - top_sector_constituents (List[Dict]: symbol, name, change_pct) [New]
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
        # Sort by change
        constituents.sort(key=lambda x: x['change_pct'], reverse=True)

        return {
            "timestamp": time.time(),
            "volume": self.base_volume * (1 + random.uniform(-0.2, 0.5)),
            "index_change_pct": self.trend + random.uniform(-0.2, 0.2),
            "north_bound_flow": random.uniform(-10000000, 10000000) + (self.trend * 5000000),
            "limit_down_count": int(max(0, 5 - self.trend * 5 + random.randint(-1, 2))),
            "bomb_rate": max(0, min(100, 20 - self.trend * 10 + random.uniform(-5, 5))),
            "top_sector": sector_name,
            "top_sector_change_pct": sector_change,
            "top_sector_constituents": constituents
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
            # Sort by change pct to get the top one
            df_sector = df_sector.sort_values(by='涨跌幅', ascending=False)
            top_sector_row = df_sector.iloc[0]
            top_sector_name = top_sector_row['板块名称']
            top_sector_change = float(top_sector_row['涨跌幅'])
            
            # 3. Get Top Constituents for the Top Sector
            # This is the Level 2 Drill-down
            top_sector_constituents = []
            try:
                # stock_board_industry_cons_em(symbol="板块名称")
                df_cons = ak.stock_board_industry_cons_em(symbol=top_sector_name)
                # Sort by change pct
                df_cons = df_cons.sort_values(by='涨跌幅', ascending=False)
                # Take top 3
                for _, row in df_cons.head(3).iterrows():
                    top_sector_constituents.append({
                        "name": row['名称'],
                        "symbol": row['代码'],
                        "change_pct": float(row['涨跌幅'])
                    })
            except Exception as e:
                print(f"Error fetching constituents for {top_sector_name}: {e}")

            # 4. Limit Up Count (Optional, can be heavy)
            # For now, we skip full limit up pool scan to keep it fast, 
            # or we can use a summary interface if available.
            limit_down_count = 0 
            bomb_rate = 0

            return {
                "timestamp": time.time(),
                "volume": volume,
                "index_change_pct": index_change,
                "north_bound_flow": 0, # Placeholder
                "limit_down_count": limit_down_count, 
                "bomb_rate": bomb_rate,
                "top_sector": top_sector_name,
                "top_sector_change_pct": top_sector_change,
                "top_sector_constituents": top_sector_constituents
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
                "top_sector_constituents": []
            }

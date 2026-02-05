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
        """
        pass

class MockDataProvider(DataProvider):
    """
    Generates random market data for testing/simulation.
    """
    def __init__(self):
        self.base_volume = 1000000
        self.trend = 0 # -1 to 1
        
    def get_latest_market_snapshot(self) -> Dict[str, Any]:
        # Simulate some random walk
        self.trend += random.uniform(-0.1, 0.1)
        self.trend = max(-1, min(1, self.trend))
        
        return {
            "timestamp": time.time(),
            "volume": self.base_volume * (1 + random.uniform(-0.2, 0.5)),
            "index_change_pct": self.trend + random.uniform(-0.2, 0.2),
            "north_bound_flow": random.uniform(-10000000, 10000000) + (self.trend * 5000000),
            "limit_down_count": int(max(0, 5 - self.trend * 5 + random.randint(-1, 2))),
            "bomb_rate": max(0, min(100, 20 - self.trend * 10 + random.uniform(-5, 5))),
            "top_sector": random.choice(["Semiconductor", "Banking", "Liquor", "New Energy", "Medicine"]),
            "top_sector_change_pct": self.trend * 2 + random.uniform(-0.5, 0.5)
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
            # stock_zh_index_spot returns a dataframe with all indices
            # We filter for sh000001
            df_index = ak.stock_zh_index_spot()
            sh_index = df_index[df_index['代码'] == 'sh000001'].iloc[0]
            
            volume = float(sh_index['成交额']) if '成交额' in sh_index else 0
            index_change = float(sh_index['涨跌幅']) if '涨跌幅' in sh_index else 0.0

            # 2. Get Top Sector (Industry Board)
            # stock_board_industry_name_em returns industry rankings
            df_sector = ak.stock_board_industry_name_em()
            top_sector_row = df_sector.iloc[0]
            top_sector_name = top_sector_row['板块名称']
            top_sector_change = float(top_sector_row['涨跌幅'])

            # 3. North Bound Flow (Simulated/Placeholder for stability as API varies)
            # Real-time north bound flow often requires specific interfaces
            north_flow = 0 

            return {
                "timestamp": time.time(),
                "volume": volume,
                "index_change_pct": index_change,
                "north_bound_flow": north_flow,
                "limit_down_count": 0, # Expensive to calculate in real-time
                "bomb_rate": 0,        # Expensive to calculate in real-time
                "top_sector": top_sector_name,
                "top_sector_change_pct": top_sector_change
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
                "top_sector_change_pct": 0
            }

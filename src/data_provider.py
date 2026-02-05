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
            # 1. Get Index Spot Data (e.g., Shanghai Composite 000001)
            # Note: Real-time API calls can be slow. In production, these should be async or cached.
            
            # Using a fast spot interface for demo (stock_zh_a_spot_em is heavy, using index)
            # sh_index = ak.stock_zh_index_spot_sina() # This is just an example
            
            # For MVP stability, we will fetch simplified data or catch errors
            # Here we simulate the logic of mapping AkShare data to our schema
            
            # Real implementation would be:
            # df_index = ak.stock_zh_index_spot() 
            # row = df_index[df_index['代码'] == 'sh000001']
            
            # Mocking the mapping for now to ensure code runs if user installs akshare
            # but API might change or network might fail.
            
            return {
                "timestamp": time.time(),
                "volume": 0, # Placeholder
                "index_change_pct": 0.0,
                "north_bound_flow": 0,
                "limit_down_count": 0,
                "bomb_rate": 0,
                "top_sector": "Unknown",
                "top_sector_change_pct": 0.0
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

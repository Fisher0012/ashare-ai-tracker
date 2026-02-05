import yfinance as yf
import pandas as pd

def get_valuation_metrics(ticker_symbol):
    print(f"Fetching data for {ticker_symbol}...")
    stock = yf.Ticker(ticker_symbol)
    
    # Get basic info
    try:
        info = stock.info
    except Exception as e:
        print(f"Error fetching info: {e}")
        return

    # 1. Current Price
    current_price = info.get('currentPrice', info.get('regularMarketPrice'))
    
    # 2. Revenue (TTM)
    revenue = info.get('totalRevenue')
    
    # 3. Free Cash Flow
    fcf = info.get('freeCashflow')
    
    # 4. Growth Rates
    rev_growth = info.get('revenueGrowth') 
    earnings_growth = info.get('earningsGrowth')
    
    # 5. Beta
    beta = info.get('beta')
    
    # 6. Analyst Estimates
    target_mean = info.get('targetMeanPrice')
    target_median = info.get('targetMedianPrice')
    recommendation = info.get('recommendationKey')
    
    # 7. Risk Free Rate (10Y Treasury)
    try:
        tnx = yf.Ticker("^TNX")
        # Get last 5 days to ensure we get a close price even if today is weekend/holiday
        hist = tnx.history(period="5d")
        if not hist.empty:
            risk_free_rate = hist['Close'].iloc[-1] / 100
        else:
            risk_free_rate = 0.04 # Fallback assumption 4%
    except Exception:
        risk_free_rate = 0.04 # Fallback
    
    # 8. Shares Outstanding
    shares_outstanding = info.get('sharesOutstanding')

    print("\n" + "="*40)
    print(f"  {ticker_symbol} Valuation Data Overview")
    print("="*40)
    
    print(f"Current Price: ${current_price}")
    print(f"Total Revenue (TTM): ${revenue}")
    print(f"Free Cash Flow (TTM): ${fcf}")
    print(f"Shares Outstanding: {shares_outstanding}")
    
    print(f"Revenue Growth (YoY): {rev_growth}")
    print(f"Earnings Growth (YoY): {earnings_growth}")
    
    print("-" * 20)
    print("【WACC Components】")
    print(f"Beta: {beta}")
    print(f"Risk Free Rate: {risk_free_rate:.4f}")
    
    print("-" * 20)
    print("【Analyst Estimates】")
    print(f"Target Mean: ${target_mean}")
    print(f"Target Median: ${target_median}")
    print(f"Recommendation: {recommendation}")

if __name__ == "__main__":
    get_valuation_metrics("NVDA")

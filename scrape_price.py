"""
AMZN Price Data Scraper using yfinance

Fetches daily price data for AMZN and adds close prices to the 10-Q filing data.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def scrape_amzn_prices():
    """
    Scrape daily price data for AMZN and add close prices to 10-Q filing data.
    """
    print("=" * 60)
    print("🚀 Starting AMZN Price Data Scraper")
    print("=" * 60)
    
    # Step 1: Fetch daily price data for AMZN
    print("\n📈 Fetching daily price data for AMZN...")
    ticker = yf.Ticker("AMZN")
    
    # Get historical data - go back 2 years to cover all filing dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # 2 years
    
    price_data = ticker.history(start=start_date, end=end_date)
    
    if price_data.empty:
        print("❌ No price data retrieved")
        return None
    
    print(f"✓ Retrieved {len(price_data)} days of price data")
    print(f"  Date range: {price_data.index[0].date()} to {price_data.index[-1].date()}")
    
    # Convert index to date (remove time component)
    price_data.index = price_data.index.date
    
    # Step 2: Read the 10-Q filing data
    print("\n📄 Reading 10-Q filing data...")
    try:
        filing_data = pd.read_csv('amzn_10q_data.csv')
        print(f"✓ Loaded {len(filing_data)} filings")
    except FileNotFoundError:
        print("❌ amzn_10q_data.csv not found")
        return None
    
    # Step 3: Match filing dates with close prices
    print("\n🔗 Matching filing dates with close prices...")
    
    close_prices = []
    
    for idx, row in filing_data.iterrows():
        filing_date_str = row['filing_date']
        
        # Parse the filing date
        try:
            filing_date = pd.to_datetime(filing_date_str).date()
        except:
            print(f"  ⚠️  Could not parse date: {filing_date_str}")
            close_prices.append(None)
            continue
        
        # Try to find the close price on the filing date
        if filing_date in price_data.index:
            close_price = price_data.loc[filing_date, 'Close']
            close_prices.append(close_price)
            print(f"  ✓ {filing_date_str}: ${close_price:,.2f}")
        else:
            # If exact date not found, try the next trading day
            # Find the next available date
            available_dates = price_data.index[price_data.index >= filing_date]
            if len(available_dates) > 0:
                next_date = available_dates[0]
                close_price = price_data.loc[next_date, 'Close']
                close_prices.append(close_price)
                print(f"  ✓ {filing_date_str} (using {next_date}): ${close_price:,.2f}")
            else:
                # Try previous trading day
                available_dates = price_data.index[price_data.index <= filing_date]
                if len(available_dates) > 0:
                    prev_date = available_dates[-1]
                    close_price = price_data.loc[prev_date, 'Close']
                    close_prices.append(close_price)
                    print(f"  ✓ {filing_date_str} (using {prev_date}): ${close_price:,.2f}")
                else:
                    close_prices.append(None)
                    print(f"  ⚠️  No price data found for {filing_date_str}")
    
    # Step 4: Add close price column to filing data
    filing_data['close_price'] = close_prices
    
    # Step 5: Save updated data
    print("\n💾 Saving updated data...")
    filing_data.to_csv('amzn_10q_data.csv', index=False)
    print("✅ Saved to: amzn_10q_data.csv")
    
    # Display results
    print("\n" + "=" * 80)
    print("📊 UPDATED 10-Q DATA WITH PRICES")
    print("=" * 80)
    print(filing_data.to_string(index=False))
    
    return filing_data, price_data


if __name__ == "__main__":
    scrape_amzn_prices()

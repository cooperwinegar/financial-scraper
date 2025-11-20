"""
AMZN 10-Q Financial Data Scraper using edgartools

This version uses the edgartools library which is much simpler and more reliable
than web scraping with Selenium.
"""

from edgar import *
import pandas as pd
from datetime import datetime

# Set your identity (required by SEC)
set_identity("Cooper Winegar cooperwinegar@gmail.com")

def scrape_amzn_10q(num_filings=5):
    """
    Scrape AMZN 10-Q filings using edgartools.
    
    Args:
        num_filings: Number of recent 10-Q filings to scrape
    """
    print("=" * 60)
    print("🚀 Starting AMZN 10-Q Financial Data Scraper (edgartools)")
    print("=" * 60)
    
    # Get Amazon company
    amazon = Company("AMZN")
    
    # Get recent 10-Q filings
    print(f"\n🔍 Fetching {num_filings} recent 10-Q filings...")
    filings = amazon.get_filings(form="10-Q").head(num_filings)
    
    results = []
    
    for i, filing in enumerate(filings, 1):
        print(f"\n{'='*60}")
        print(f"📊 Processing Filing {i}/{len(filings)}")
        print(f"{'='*60}")
        print(f"  Filing Date: {filing.filing_date}")
        print(f"  Accession Number: {filing.accession_number}")
        
        try:
            # Get the filing object
            filing_obj = filing.obj()
            
            # Get financials (it's a property, not a method)
            print("  📈 Extracting financial data...")
            financials = filing_obj.financials
            
            # Extract financial data
            data = {
                'filing_date': filing.filing_date.strftime('%Y-%m-%d') if filing.filing_date else None,
                'accession_number': filing.accession_number,
                'net_income': None,
                'preferred_dividends': None,
                'weighted_avg_shares': None
            }
            
            if financials:
                # Get net income using the method
                try:
                    net_income = financials.get_net_income()
                    if net_income is not None:
                        # If it's a Series or DataFrame, get the first value
                        if isinstance(net_income, pd.Series):
                            data['net_income'] = net_income.iloc[0] if len(net_income) > 0 else None
                        elif isinstance(net_income, (int, float)):
                            data['net_income'] = net_income
                        if data['net_income']:
                            print(f"    ✓ Found Net Income: ${data['net_income']:,.2f}")
                except Exception as e:
                    print(f"    ⚠️  Error getting net income: {e}")
                
                # Get preferred dividends and weighted average shares
                try:
                    # income_statement is a method that returns a Statement object
                    income_stmt_obj = financials.income_statement()
                    if income_stmt_obj is not None:
                        # Convert Statement to DataFrame if it has that method
                        if hasattr(income_stmt_obj, 'to_dataframe'):
                            income_stmt = income_stmt_obj.to_dataframe()
                        elif hasattr(income_stmt_obj, 'dataframe'):
                            income_stmt = income_stmt_obj.dataframe
                        elif isinstance(income_stmt_obj, pd.DataFrame):
                            income_stmt = income_stmt_obj
                        else:
                            # Try to access as attribute
                            income_stmt = getattr(income_stmt_obj, 'df', None) or getattr(income_stmt_obj, 'data', None)
                        
                        if income_stmt is not None and isinstance(income_stmt, pd.DataFrame):
                            # Debug: Show structure of income statement
                            print(f"    Income statement shape: {income_stmt.shape}")
                            print(f"    Income statement columns (first 3): {list(income_stmt.columns)[:3]}")
                            print(f"    Income statement index (first 15): {[str(x)[:60] for x in list(income_stmt.index)[:15]]}")
                        else:
                            print(f"    ⚠️  Could not convert income statement to DataFrame. Type: {type(income_stmt_obj)}")
                            income_stmt = None
                    else:
                        income_stmt = None
                    
                    if income_stmt is not None and isinstance(income_stmt, pd.DataFrame):
                        # The income statement has 'label' column with row descriptions
                        # and date columns with the actual values
                        
                        # Find date columns (exclude 'concept' and 'label')
                        date_columns = [col for col in income_stmt.columns if col not in ['concept', 'label']]
                        if date_columns and 'label' in income_stmt.columns:
                            # Use the first date column (most recent period)
                            value_column = date_columns[0]
                            
                            # Look for preferred dividends in the 'label' column
                            for idx in income_stmt.index:
                                label = str(income_stmt.loc[idx, 'label']).lower()
                                if 'preferred' in label and 'dividend' in label:
                                    val = income_stmt.loc[idx, value_column]
                                    if pd.notna(val) and isinstance(val, (int, float)):
                                        data['preferred_dividends'] = val
                                        print(f"    ✓ Found Preferred Dividends: ${data['preferred_dividends']:,.2f}")
                                        break
                            
                            # If not found, default to 0 (AMZN typically has no preferred dividends)
                            if data['preferred_dividends'] is None:
                                data['preferred_dividends'] = 0.0
                                print(f"    ℹ️  Preferred Dividends not found, defaulting to $0 (typical for AMZN)")
                            
                            # Look for weighted average shares in the 'label' column
                            for idx in income_stmt.index:
                                label = str(income_stmt.loc[idx, 'label']).lower()
                                # Look for various patterns
                                if ('shares' in label and ('weighted' in label or 'average' in label)) or \
                                   ('weighted' in label and 'average' in label and 'shares' in label) or \
                                   ('common' in label and 'shares' in label and 'outstanding' in label):
                                    val = income_stmt.loc[idx, value_column]
                                    if pd.notna(val) and isinstance(val, (int, float)) and val > 0:
                                        data['weighted_avg_shares'] = val
                                        print(f"    ✓ Found Weighted Avg Shares: {data['weighted_avg_shares']:,.0f}")
                                        break
                            
                            # If still not found, search all labels more broadly
                            if data['weighted_avg_shares'] is None:
                                for idx in income_stmt.index:
                                    label = str(income_stmt.loc[idx, 'label']).lower()
                                    if 'shares' in label:
                                        val = income_stmt.loc[idx, value_column]
                                        if pd.notna(val) and isinstance(val, (int, float)) and val > 1000000:  # Shares should be in millions
                                            data['weighted_avg_shares'] = val
                                            print(f"    ✓ Found Weighted Avg Shares (broad search): {data['weighted_avg_shares']:,.0f}")
                                            break
                    else:
                        print(f"    ⚠️  Income statement is not a DataFrame: {type(income_stmt)}")
                except Exception as e:
                    print(f"    ⚠️  Error getting preferred dividends/shares: {e}")
                    import traceback
                    traceback.print_exc()
                    if data['preferred_dividends'] is None:
                        data['preferred_dividends'] = 0.0
                
            
            results.append(data)
            
        except Exception as e:
            print(f"    ❌ Error processing filing: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Display results
    print("\n" + "=" * 80)
    print("📈 SCRAPED FINANCIAL DATA")
    print("=" * 80)
    
    if results:
        df = pd.DataFrame(results)
        print(df.to_string(index=False))
        
        print("\n" + "=" * 80)
        print("💾 Saving results to CSV...")
        df.to_csv('amzn_10q_data.csv', index=False)
        print("✅ Saved to: amzn_10q_data.csv")
        
        return df
    else:
        print("⚠️  No data was scraped.")
        return None


if __name__ == "__main__":
    # Scrape recent 10-Q filings
    scrape_amzn_10q()


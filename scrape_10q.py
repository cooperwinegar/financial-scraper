"""
AMZN 10-Q Financial Data Scraper

This script scrapes Amazon's recent 10-Q filings from the SEC EDGAR database
to extract:
- Net Income
- Preferred Dividends
- Weighted Average Common Shares Outstanding

The script uses Selenium with a visible browser so you can see the scraping process.
"""

import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime


class AMZN10QScraper:
    """
    Scraper for AMZN 10-Q filings from SEC EDGAR.
    
    How it works:
    1. Navigates to SEC EDGAR search for AMZN
    2. Filters for 10-Q filings
    3. Opens each recent 10-Q filing
    4. Searches for the financial statements (typically in the HTML or XBRL format)
    5. Extracts net income, preferred dividends, and weighted average shares
    6. Displays results in a structured format
    """
    
    def __init__(self, headless=False):
        """
        Initialize the scraper with a visible browser.
        
        Args:
            headless: If False, browser will be visible so you can watch the scraping
        """
        self.headless = headless
        self.driver = None
        self.results = []
        
    def setup_driver(self):
        """Set up Chrome driver with visible browser."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        else:
            chrome_options.add_argument('--start-maximized')
        
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)
        
    def get_recent_10q_filings(self, ticker="AMZN", num_filings=5):
        """
        Navigate to SEC EDGAR and get links to recent 10-Q filings.
        
        Args:
            ticker: Stock ticker symbol (default: AMZN)
            num_filings: Number of recent 10-Q filings to retrieve
        """
        print(f"\n🔍 Searching for {ticker} 10-Q filings on SEC EDGAR...")
        
        # SEC EDGAR company search URL
        search_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-Q&dateb=&owner=exclude&count={num_filings}"
        
        print(f"📍 Navigating to: {search_url}")
        self.driver.get(search_url)
        time.sleep(2)  # Allow page to load
        
        # Find all 10-Q filing links
        filing_links = []
        try:
            # SEC EDGAR typically has links in a table
            links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/Archives/edgar/data/')]")
            
            for link in links[:num_filings]:
                href = link.get_attribute('href')
                if '10-Q' in href or '10q' in href.lower():
                    filing_links.append(href)
                    print(f"  ✓ Found 10-Q filing: {href}")
            
            # Also try finding by text content
            if not filing_links:
                table_rows = self.driver.find_elements(By.TAG_NAME, "tr")
                for row in table_rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) > 1:
                        for cell in cells:
                            links_in_cell = cell.find_elements(By.TAG_NAME, "a")
                            for link in links_in_cell:
                                href = link.get_attribute('href')
                                if href and ('10-Q' in href or '10q' in href.lower()):
                                    if href not in filing_links:
                                        filing_links.append(href)
                                        print(f"  ✓ Found 10-Q filing: {href}")
            
        except Exception as e:
            print(f"  ⚠️  Error finding filing links: {e}")
        
        return filing_links[:num_filings]
    
    def get_filing_document_url(self, filing_url):
        """
        Navigate to a filing page and find the actual document URL.
        Usually the first "10-Q" or "10q" document link.
        """
        print(f"\n  📄 Opening filing page: {filing_url}")
        self.driver.get(filing_url)
        time.sleep(2)
        
        # Look for the document link (usually in a table)
        try:
            # Try to find links that contain the document
            links = self.driver.find_elements(By.XPATH, "//a[contains(text(), '10-Q') or contains(text(), '10q')]")
            if not links:
                links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '.htm')]")
            
            for link in links:
                href = link.get_attribute('href')
                if href and ('.htm' in href.lower() or '.html' in href.lower()):
                    if '10-Q' in link.text or '10q' in link.text.lower():
                        full_url = href if href.startswith('http') else f"https://www.sec.gov{href}"
                        print(f"    ✓ Found document: {full_url}")
                        return full_url
        except Exception as e:
            print(f"    ⚠️  Error finding document: {e}")
        
        return None
    
    def extract_financial_data(self, document_url):
        """
        Extract financial data from a 10-Q document.
        
        Looks for:
        - Net Income
        - Preferred Dividends
        - Weighted Average Common Shares Outstanding
        """
        print(f"\n    🔎 Extracting financial data from document...")
        self.driver.get(document_url)
        time.sleep(3)  # Allow page to fully load
        
        # Get page source and parse with BeautifulSoup
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Extract text content
        text_content = soup.get_text()
        
        # Initialize data dictionary
        data = {
            'net_income': None,
            'preferred_dividends': None,
            'weighted_avg_shares': None
        }
        
        # Pattern matching for financial data
        # Net Income patterns (in millions, could be negative)
        net_income_patterns = [
            r'Net\s+income[:\s]+[\$\(]?([\d,]+(?:\.\d+)?)',
            r'Net\s+earnings[:\s]+[\$\(]?([\d,]+(?:\.\d+)?)',
            r'Net\s+income\s+\(loss\)[:\s]+[\$\(]?([\d,]+(?:\.\d+)?)',
        ]
        
        # Preferred Dividends patterns
        preferred_dividends_patterns = [
            r'Preferred\s+stock\s+dividends[:\s]+[\$\(]?([\d,]+(?:\.\d+)?)',
            r'Dividends\s+on\s+preferred\s+stock[:\s]+[\$\(]?([\d,]+(?:\.\d+)?)',
        ]
        
        # Weighted Average Shares patterns
        shares_patterns = [
            r'Weighted[-\s]+average\s+common\s+shares\s+outstanding[:\s]+([\d,]+(?:\.\d+)?)',
            r'Weighted[-\s]+average\s+shares\s+outstanding[:\s]+([\d,]+(?:\.\d+)?)',
            r'Average\s+shares\s+outstanding[:\s]+([\d,]+(?:\.\d+)?)',
        ]
        
        # Search for Net Income
        for pattern in net_income_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                value = match.group(1).replace(',', '')
                try:
                    data['net_income'] = float(value)
                    print(f"      ✓ Found Net Income: ${data['net_income']:,.2f} million")
                    break
                except ValueError:
                    continue
        
        # Search for Preferred Dividends (often 0 for AMZN)
        for pattern in preferred_dividends_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                value = match.group(1).replace(',', '')
                try:
                    data['preferred_dividends'] = float(value)
                    print(f"      ✓ Found Preferred Dividends: ${data['preferred_dividends']:,.2f} million")
                    break
                except ValueError:
                    continue
        
        # If not found, AMZN typically has $0 preferred dividends
        if data['preferred_dividends'] is None:
            data['preferred_dividends'] = 0.0
            print(f"      ℹ️  Preferred Dividends not found, defaulting to $0 (typical for AMZN)")
        
        # Search for Weighted Average Shares
        for pattern in shares_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                value = match.group(1).replace(',', '')
                try:
                    data['weighted_avg_shares'] = float(value)
                    print(f"      ✓ Found Weighted Avg Shares: {data['weighted_avg_shares']:,.0f} million")
                    break
                except ValueError:
                    continue
        
        # Also try to find data in HTML tables (more reliable)
        tables = soup.find_all('table')
        for table in tables:
            table_text = table.get_text()
            rows = table.find_all('tr')
            
            for row in rows:
                cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                row_text = ' '.join(cells).lower()
                
                # Check for net income in table
                if 'net income' in row_text or 'net earnings' in row_text:
                    for cell in cells:
                        # Look for numbers (could be in millions)
                        numbers = re.findall(r'[\$\(]?([\d,]+(?:\.\d+)?)', cell)
                        if numbers:
                            try:
                                value = float(numbers[0].replace(',', ''))
                                if data['net_income'] is None or abs(value) > abs(data['net_income']):
                                    data['net_income'] = value
                                    print(f"      ✓ Found Net Income in table: ${value:,.2f} million")
                            except ValueError:
                                continue
                
                # Check for shares outstanding
                if 'weighted average' in row_text and 'shares' in row_text:
                    for cell in cells:
                        numbers = re.findall(r'([\d,]+(?:\.\d+)?)', cell)
                        if numbers:
                            try:
                                value = float(numbers[0].replace(',', ''))
                                if value > 1000:  # Shares should be in millions or large numbers
                                    data['weighted_avg_shares'] = value
                                    print(f"      ✓ Found Weighted Avg Shares in table: {value:,.0f} million")
                            except ValueError:
                                continue
        
        return data
    
    def scrape(self, ticker="AMZN", num_filings=5):
        """
        Main scraping method.
        
        Args:
            ticker: Stock ticker symbol
            num_filings: Number of recent 10-Q filings to scrape
        """
        print("=" * 60)
        print(f"🚀 Starting AMZN 10-Q Financial Data Scraper")
        print("=" * 60)
        
        self.setup_driver()
        
        try:
            # Get recent 10-Q filing links
            filing_links = self.get_recent_10q_filings(ticker, num_filings)
            
            if not filing_links:
                print("\n❌ No 10-Q filings found. Trying alternative approach...")
                # Alternative: Direct SEC EDGAR search
                cik_url = f"https://www.sec.gov/cgi-bin/browse-edgar?CIK=0001018724&action=getcompany"
                print(f"📍 Trying direct CIK search: {cik_url}")
                self.driver.get(cik_url)
                time.sleep(3)
                filing_links = self.get_recent_10q_filings(ticker, num_filings)
            
            if not filing_links:
                print("\n❌ Could not find 10-Q filings. Please check the SEC EDGAR website manually.")
                return
            
            # Scrape each filing
            for i, filing_url in enumerate(filing_links, 1):
                print(f"\n{'='*60}")
                print(f"📊 Processing Filing {i}/{len(filing_links)}")
                print(f"{'='*60}")
                
                document_url = self.get_filing_document_url(filing_url)
                if document_url:
                    data = self.extract_financial_data(document_url)
                    data['filing_url'] = filing_url
                    data['document_url'] = document_url
                    data['filing_date'] = datetime.now().strftime('%Y-%m-%d')
                    self.results.append(data)
                else:
                    print(f"    ⚠️  Could not find document for this filing")
                
                time.sleep(2)  # Be respectful with requests
            
        except Exception as e:
            print(f"\n❌ Error during scraping: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n" + "=" * 60)
            print("✅ Scraping complete!")
            print("=" * 60)
            # Keep browser open for a few seconds so user can see
            time.sleep(5)
            if self.driver:
                self.driver.quit()
    
    def display_results(self):
        """Display the scraped results in a formatted table."""
        if not self.results:
            print("\n⚠️  No data was scraped.")
            return
        
        print("\n" + "=" * 80)
        print("📈 SCRAPED FINANCIAL DATA")
        print("=" * 80)
        
        df = pd.DataFrame(self.results)
        print(df.to_string(index=False))
        
        print("\n" + "=" * 80)
        print("💾 Saving results to CSV...")
        df.to_csv('amzn_10q_data.csv', index=False)
        print("✅ Saved to: amzn_10q_data.csv")
        
        return df


if __name__ == "__main__":
    # Create scraper with visible browser (headless=False)
    scraper = AMZN10QScraper(headless=False)
    
    # Scrape recent 10-Q filings
    scraper.scrape(ticker="AMZN", num_filings=3)
    
    # Display results
    scraper.display_results()


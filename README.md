# AMZN 10-Q Financial Data Scraper

A Python scraper to extract financial data from Amazon's (AMZN) recent 10-Q quarterly filings from the SEC EDGAR database.

## What It Scrapes

The scraper extracts the following financial metrics from each 10-Q filing:
- **Net Income** - The company's net earnings for the quarter
- **Preferred Dividends** - Dividends paid on preferred stock (typically $0 for AMZN)
- **Weighted Average Common Shares Outstanding** - Average number of common shares outstanding during the period

## How It Works

### Architecture Overview

1. **Browser Automation (Selenium)**: Uses Selenium with Chrome to navigate the SEC EDGAR website. The browser is visible by default so you can watch the scraping process in real-time.

2. **SEC EDGAR Navigation**:
   - Navigates to the SEC EDGAR company search page for AMZN
   - Filters for 10-Q filings
   - Collects links to recent 10-Q filings

3. **Document Extraction**:
   - Opens each 10-Q filing page
   - Finds the actual HTML document link
   - Loads the full 10-Q document

4. **Data Extraction**:
   - Uses BeautifulSoup to parse the HTML
   - Searches for financial data using:
     - **Regex patterns** to find specific financial terms and values
     - **HTML table parsing** to extract structured data from financial tables
   - Handles various formats and presentations of the data

5. **Data Storage**:
   - Stores results in a pandas DataFrame
   - Exports to CSV file (`amzn_10q_data.csv`)

### Key Features

- **Visible Browser**: Watch the scraper navigate and extract data in real-time
- **Robust Pattern Matching**: Multiple regex patterns to find financial data in various formats
- **Table Parsing**: Extracts data from HTML tables when available
- **Error Handling**: Gracefully handles missing data or connection issues
- **Respectful Scraping**: Includes delays between requests to be respectful to SEC servers

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. The script will automatically download ChromeDriver using `webdriver-manager`, so no manual setup needed.

## Usage

Run the scraper:
```bash
python scrape_10q.py
```

The script will:
1. Open a Chrome browser window (you'll see it navigate)
2. Search for AMZN's recent 10-Q filings
3. Open each filing and extract the financial data
4. Display results in the terminal
5. Save results to `amzn_10q_data.csv`

### Customization

You can modify the script to:
- Change the number of filings to scrape (default: 3)
- Run in headless mode (browser not visible)
- Add additional financial metrics to extract
- Change the ticker symbol

## Output

The scraper generates:
- **Terminal output**: Real-time progress and extracted data
- **CSV file**: `amzn_10q_data.csv` with all scraped data

## Notes

- SEC EDGAR documents can vary in format, so the scraper uses multiple extraction methods
- Some values may be in millions or other units - check the actual filings for context
- The scraper includes delays to be respectful to SEC servers
- If data is not found, it will be marked as `None` in the results

## Future Enhancements

Potential improvements:
- Extract data from XBRL format (more structured)
- Add more financial metrics (revenue, EPS, etc.)
- Handle annual 10-K filings
- Add data validation and cleaning
- Create visualizations of the data


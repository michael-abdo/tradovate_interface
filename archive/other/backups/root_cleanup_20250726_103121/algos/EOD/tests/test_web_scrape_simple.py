#!/usr/bin/env python3
"""
Simple test of web scraping with visible browser for debugging
"""

import sys
import os
import time

# Add the barchart_web_scraper directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tasks/options_trading_system/data_ingestion/barchart_web_scraper'))

from solution import BarchartWebScraper

def test_simple_scrape():
    """Test basic web scraping with visible browser"""
    
    print("🌐 Testing Barchart Web Scraping (Visible Browser)")
    print("=" * 60)
    
    # URL to scrape
    url = "https://www.barchart.com/futures/quotes/NQM25/options/MC7M25?futuresOptionsView=merged"
    
    # Initialize scraper with visible browser
    print("\n⚠️  Browser will open - DO NOT CLOSE IT")
    print("⏱️  Will wait 10 seconds for page to load")
    
    scraper = BarchartWebScraper(headless=False)
    
    try:
        print(f"\n📊 Scraping: {url}")
        print("Please watch the browser window...\n")
        
        # Scrape the page
        web_data = scraper.scrape_barchart_options(url)
        
        print(f"\n✅ Successfully scraped {web_data.total_contracts} contracts")
        print(f"📊 Web Data Summary:")
        print(f"   - Symbol: {web_data.underlying_symbol}")
        print(f"   - Expiration: {web_data.expiration_date}")
        print(f"   - Underlying Price: ${web_data.underlying_price or 'Not found'}")
        print(f"   - Source: {web_data.source}")
        
        # Show first few contracts
        if web_data.contracts:
            print(f"\n📋 First 5 contracts:")
            for i, contract in enumerate(web_data.contracts[:5]):
                print(f"   {i+1}. Strike ${contract.strike:,.0f}")
                if contract.call_last:
                    print(f"      - Call: ${contract.call_last}")
                if contract.put_last:
                    print(f"      - Put: ${contract.put_last}")
        
    except Exception as e:
        print(f"\n❌ Scraping failed: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n🔍 Troubleshooting tips:")
        print("1. Check if the page loaded correctly in the browser")
        print("2. Look for any popups or cookie banners blocking the page")
        print("3. Check if the table structure has changed")
        print("4. Try updating the Chrome driver")

if __name__ == "__main__":
    test_simple_scrape()
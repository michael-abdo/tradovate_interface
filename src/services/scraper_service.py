"""
Scraper Service for managing Tradovate market data
Handles data persistence, retrieval, and export functionality
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import deque
import threading

from ..utils.core import get_project_root

class ScraperService:
    """Service for managing scraped Tradovate market data"""
    
    def __init__(self, buffer_size: int = 1000, persist_interval: int = 60):
        """
        Initialize the scraper service
        
        Args:
            buffer_size: Maximum number of trades to keep in memory
            persist_interval: Seconds between automatic persistence
        """
        self.project_root = get_project_root()
        self.data_dir = self.project_root / 'data' / 'scraped_trades'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory buffer for real-time data
        self.trade_buffer = deque(maxlen=buffer_size)
        self.latest_data = {}
        self.scraper_status = {
            'enabled': False,
            'last_update': None,
            'trades_captured': 0,
            'accounts': {}
        }
        
        # Thread-safe lock
        self.lock = threading.Lock()
        
        # Persistence settings
        self.persist_interval = persist_interval
        self.last_persist_time = time.time()
        
        # Load existing data
        self.load_today_data()
    
    def add_scraped_data(self, account: str, data: Dict[str, Any]) -> None:
        """
        Add new scraped data from a Chrome instance
        
        Args:
            account: Account identifier
            data: Scraped data dictionary
        """
        with self.lock:
            # Update latest data for account
            self.latest_data[account] = data
            
            # Add trades to buffer
            if 'trades' in data:
                for trade in data['trades']:
                    trade['account'] = account
                    trade['captured_at'] = data.get('timestamp', datetime.now().isoformat())
                    self.trade_buffer.append(trade)
            
            # Update status
            self.scraper_status['enabled'] = True
            self.scraper_status['last_update'] = datetime.now().isoformat()
            self.scraper_status['trades_captured'] += len(data.get('trades', []))
            self.scraper_status['accounts'][account] = {
                'last_update': data.get('timestamp'),
                'symbol': data.get('contractInfo', {}).get('name', 'Unknown'),
                'trades': len(data.get('trades', []))
            }
            
            # Auto-persist if interval exceeded
            if time.time() - self.last_persist_time > self.persist_interval:
                self.persist_data()
    
    def get_latest_data(self, account: Optional[str] = None) -> Dict[str, Any]:
        """Get the latest scraped data"""
        with self.lock:
            if account:
                return self.latest_data.get(account, {})
            return self.latest_data
    
    def get_recent_trades(self, limit: int = 100, account: Optional[str] = None) -> List[Dict]:
        """Get recent trades from buffer"""
        with self.lock:
            trades = list(self.trade_buffer)
            
            if account:
                trades = [t for t in trades if t.get('account') == account]
            
            # Return most recent trades
            return trades[-limit:] if len(trades) > limit else trades
    
    def get_status(self) -> Dict[str, Any]:
        """Get scraper service status"""
        with self.lock:
            return self.scraper_status.copy()
    
    def persist_data(self) -> None:
        """Persist current buffer to disk"""
        with self.lock:
            if not self.trade_buffer:
                return
            
            # Create filename with date
            date_str = datetime.now().strftime('%Y-%m-%d')
            filename = f"{date_str}_trades.json"
            filepath = self.data_dir / filename
            
            # Load existing data if file exists
            existing_data = []
            if filepath.exists():
                try:
                    with open(filepath, 'r') as f:
                        existing_data = json.load(f)
                except:
                    existing_data = []
            
            # Append new trades
            new_trades = list(self.trade_buffer)
            all_trades = existing_data + new_trades
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump(all_trades, f, indent=2)
            
            # Clear buffer after persisting
            self.trade_buffer.clear()
            self.last_persist_time = time.time()
            
            print(f"[Scraper Service] Persisted {len(new_trades)} trades to {filename}")
    
    def load_today_data(self) -> None:
        """Load today's data into buffer"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"{date_str}_trades.json"
        filepath = self.data_dir / filename
        
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    trades = json.load(f)
                    # Load only recent trades into buffer
                    recent_cutoff = datetime.now() - timedelta(hours=1)
                    for trade in trades:
                        trade_time = datetime.fromisoformat(trade.get('captured_at', ''))
                        if trade_time > recent_cutoff:
                            self.trade_buffer.append(trade)
                    
                    print(f"[Scraper Service] Loaded {len(self.trade_buffer)} recent trades")
            except Exception as e:
                print(f"[Scraper Service] Error loading trades: {e}")
    
    def export_data(self, format: str = 'json', start_date: Optional[str] = None, 
                   end_date: Optional[str] = None) -> tuple[bytes, str]:
        """
        Export scraped data in specified format
        
        Args:
            format: Export format ('json' or 'csv')
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            
        Returns:
            Tuple of (data_bytes, filename)
        """
        # Persist current buffer first
        self.persist_data()
        
        # Determine date range
        if not start_date:
            start_date = datetime.now().strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Collect all trades in date range
        all_trades = []
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        while current_date <= end:
            date_str = current_date.strftime('%Y-%m-%d')
            filepath = self.data_dir / f"{date_str}_trades.json"
            
            if filepath.exists():
                try:
                    with open(filepath, 'r') as f:
                        trades = json.load(f)
                        all_trades.extend(trades)
                except:
                    pass
            
            current_date += timedelta(days=1)
        
        # Format data
        if format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            if all_trades:
                fieldnames = ['captured_at', 'account', 'timestamp', 'price', 
                             'size', 'accumulatedVolume', 'tickDirection']
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                
                for trade in all_trades:
                    row = {k: trade.get(k, '') for k in fieldnames}
                    writer.writerow(row)
            
            data = output.getvalue().encode('utf-8')
            filename = f"tradovate_trades_{start_date}_to_{end_date}.csv"
        else:
            # JSON format
            data = json.dumps(all_trades, indent=2).encode('utf-8')
            filename = f"tradovate_trades_{start_date}_to_{end_date}.json"
        
        return data, filename
    
    def clear_old_data(self, days_to_keep: int = 7) -> None:
        """Remove data files older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for filepath in self.data_dir.glob("*_trades.json"):
            try:
                # Extract date from filename
                date_str = filepath.stem.split('_')[0]
                file_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                if file_date < cutoff_date:
                    filepath.unlink()
                    print(f"[Scraper Service] Removed old data file: {filepath.name}")
            except:
                pass


# Global instance
_scraper_service = None

def get_scraper_service() -> ScraperService:
    """Get or create the global scraper service instance"""
    global _scraper_service
    if _scraper_service is None:
        _scraper_service = ScraperService()
    return _scraper_service
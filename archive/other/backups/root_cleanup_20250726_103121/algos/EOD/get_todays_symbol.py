#!/usr/bin/env python3
"""
Get today's EOD symbol
"""
from datetime import datetime

# Today is Thursday, July 3rd, 2025
today = datetime.now()
month_code = {7: 'N'}[today.month]  # July = N
day_code = 4  # Thursday = 4
year = 25  # 2025

eod_symbol = f"MC{day_code}{month_code}{year}"
print(f"Today's EOD symbol: {eod_symbol}")
print(f"Date: {today.strftime('%Y-%m-%d %A')}")

# Monthly symbol
monthly_symbol = f"MC{month_code}{year}"
print(f"Monthly symbol: {monthly_symbol}")
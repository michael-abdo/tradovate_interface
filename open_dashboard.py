#!/usr/bin/env python3
"""Simple script to open dashboard in Chrome"""
import subprocess
import os

# Simple Chrome launch for dashboard
chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
url = "http://localhost:6001"

# Launch Chrome with the dashboard URL
subprocess.run([
    chrome_path,
    "--new-window",
    url
])

print(f"Opened {url} in Chrome")
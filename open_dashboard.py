#!/usr/bin/env python3
"""Simple script to open dashboard in Chrome"""
import subprocess
import os

# Chrome path and dashboard URL
chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
dashboard_url = "http://localhost:6001"
dashboard_port = 9321  # Fixed port for dashboard
profile_dir = os.path.join("/tmp", f"tradovate_dashboard_profile_{dashboard_port}")
os.makedirs(profile_dir, exist_ok=True)

# Launch Chrome with EXACT same flags as Tradovate windows
chrome_cmd = [
    chrome_path,
    f"--remote-debugging-port={dashboard_port}",
    f"--user-data-dir={profile_dir}",
    "--no-first-run",
    "--no-default-browser-check",
    "--new-window",
    "--disable-notifications",
    "--disable-popup-blocking",
    "--disable-infobars",
    "--disable-session-crashed-bubble",
    "--disable-save-password-bubble",
    "--disable-features=InfiniteSessionRestore",
    "--hide-crash-restore-bubble",
    "--no-crash-upload",
    "--disable-backgrounding-occluded-windows",
    "--disable-dev-shm-usage",
    "--no-sandbox",
    dashboard_url,
]

process = subprocess.Popen(chrome_cmd,
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)

print(f"Dashboard window opened at {dashboard_url} (PID: {process.pid})")
#!/bin/bash

echo "🚀 TRADOVATE DASHBOARD INTEGRATION TEST"
echo "======================================"
echo "Testing port 9223 integration with visible Chrome window"
echo ""

# Activate virtual environment
source venv/bin/activate

echo "1. Checking current Chrome 9223 status..."
python main.py chrome status
echo ""

echo "2. Starting Chrome 9223 (you should see a Chrome window appear)..."
python main.py chrome start
echo ""

echo "3. Starting dashboard at http://localhost:6001"
echo "You should now see:"
echo "   - A Chrome window with Tradovate loaded"
echo "   - Dashboard accessible in your browser"
echo "Press Ctrl+C to stop the dashboard when testing is complete"
echo ""

# Start the dashboard - Chrome should already be running visibly
python main.py dashboard
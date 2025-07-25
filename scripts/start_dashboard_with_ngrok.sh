#!/bin/bash

# Start Dashboard with Reserved Ngrok Domain
# Requires ngrok paid plan with reserved domain

# Your reserved domain (replace with actual reserved domain)
RESERVED_DOMAIN="your-reserved-domain.ngrok-free.app"

echo "🚀 Starting Tradovate Dashboard with Reserved Ngrok Domain"
echo "🔗 Will be available at: https://$RESERVED_DOMAIN"
echo ""

# Check if dashboard is already running
if lsof -ti:6001 > /dev/null 2>&1; then
    echo "⚠️  Dashboard already running on port 6001"
else
    echo "📱 Starting dashboard..."
    cd /Users/Mike/trading/tradovate_interface
    source venv/bin/activate
    nohup python src/dashboard.py > dashboard.log 2>&1 &
    sleep 3
fi

# Check if ngrok is already running
if lsof -ti:4040 > /dev/null 2>&1; then
    echo "⚠️  Ngrok already running"
    # Get current tunnel URL
    CURRENT_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null)
    echo "🔗 Current URL: $CURRENT_URL"
else
    echo "🌐 Starting ngrok with reserved domain..."
    # Start ngrok with reserved domain
    ngrok http 6001 --domain=$RESERVED_DOMAIN > /tmp/ngrok.log 2>&1 &
    sleep 5
    echo "✅ Ngrok started with reserved domain"
fi

echo ""
echo "🎯 Dashboard should be available at:"
echo "   Local:  http://localhost:6001"
echo "   Public: https://$RESERVED_DOMAIN"
echo ""
echo "💡 To get a reserved domain:"
echo "   1. Sign up for ngrok paid plan"
echo "   2. Reserve a domain in ngrok dashboard"
echo "   3. Update RESERVED_DOMAIN variable in this script"
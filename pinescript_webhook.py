# webhook_server.py
import subprocess
import threading
import time
import re
import sys
from flask import Flask, request, jsonify
import json
import os

# Import the TradovateController from app.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import TradovateController

app = Flask(__name__)
PORT = 6000

# Initialize the TradovateController
controller = TradovateController()

def start_ngrok(port: int) -> str | None:
    """
    Launch ngrok using a fixed domain: stonkz92224.ngrok.app
    """
    domain = "stonkz92224.ngrok.app"
    proc = subprocess.Popen(
        ["ngrok", "http", "--domain", domain, str(port), "--log", "stdout"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )

    pat = re.compile(r"url=(https?://[^\s]+)")
    for _ in range(120):  # ~12s timeout
        line = proc.stdout.readline()
        if "ERR_NGROK_15002" in line:
            proc.terminate()
            print("♨️  Error: Reserved domain requires valid ngrok plan.")
            return None
        if m := pat.search(line):
            if domain in m.group(1):
                print(f"🌐 Ngrok tunnel URL confirmed: {m.group(1)}")
                return m.group(1)
    proc.terminate()
    print("❌ Timeout: ngrok did not confirm the domain in time.")
    return None

def process_trading_signal(data):
    """
    Process incoming trading signal and execute it on Tradovate
    """
    print(f"Processing trade signal: {json.dumps(data, indent=2)}")
    
    # Extract the data from the webhook payload
    symbol = data.get("symbol", "")
    action = data.get("action", "Buy")  # Buy or Sell
    order_qty = int(data.get("orderQty", 1))
    order_type = data.get("orderType", "Market")
    entry_price = data.get("entryPrice", 0)
    tp_price = data.get("takeProfitPrice", 0)
    trade_type = data.get("tradeType", "Open")  # Open or Close
    strategy = data.get("strategy", "")
    
    # Log the strategy that sent the signal
    print(f"Strategy: {strategy}")
    
    # If this is a Close signal, use exit_positions
    if trade_type == "Close":
        print(f"🔴 Closing positions for {symbol}")
        results = controller.execute_on_all('exit_positions', symbol)
        print(f"Close results: {results}")
        return {"status": "closed", "symbol": symbol, "results": results}
    
    # Otherwise, it's an open signal - calculate TP and SL in ticks
    # Get the tick size from the first connection (assuming consistent across all)
    js_code = f"futuresTickData['{symbol.replace('USD', '')}']?.tickSize || 0.25;"
    tick_size = 0.25  # Default tick size
    
    try:
        if controller.connections:
            tick_size_result = controller.connections[0].tab.Runtime.evaluate(expression=js_code)
            if tick_size_result and 'result' in tick_size_result and 'value' in tick_size_result['result']:
                tick_size = float(tick_size_result['result']['value'])
    except Exception as e:
        print(f"Error getting tick size: {e}")
    
    # Calculate TP ticks if TP price is provided
    tp_ticks = 100  # Default TP ticks
    if tp_price and entry_price and tp_price > 0 and entry_price > 0:
        price_diff = abs(tp_price - entry_price)
        if price_diff > 0 and tick_size > 0:
            tp_ticks = int(price_diff / tick_size)
            print(f"Calculated TP ticks: {tp_ticks} (price diff: {price_diff}, tick size: {tick_size})")
    
    # Default SL ticks (typically 40% of TP)
    sl_ticks = int(tp_ticks * 0.4) if tp_ticks else 40
    
    # Execute the trade on all connected Tradovate instances
    print(f"🟢 Executing {action} order for {order_qty} {symbol} with TP: {tp_ticks} ticks, SL: {sl_ticks} ticks")
    results = controller.execute_on_all('auto_trade', 
                                symbol, order_qty, action, 
                                tp_ticks, sl_ticks, tick_size)
    
    return {
        "status": "executed", 
        "symbol": symbol, 
        "action": action,
        "quantity": order_qty,
        "tp_ticks": tp_ticks,
        "sl_ticks": sl_ticks,
        "results": results
    }

@app.route('/')
def home():
    return """
    <html>
      <head><title>Webhook Server</title></head>
      <body style="font-family: Arial, sans-serif; text-align: center; padding-top: 100px;">
        <h1>✅ Server is Running</h1>
        <p>Waiting for webhooks at <b>/webhook</b> endpoint.</p>
      </body>
    </html>
    """

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        data = request.get_json(force=True)
        print("\n✅ New webhook received:")
        print(json.dumps(data, indent=2))
        
        # Process and execute the trading signal
        if controller.connections:
            result = process_trading_signal(data)
            return jsonify(result), 200
        else:
            print("❌ No Tradovate connections available. Make sure auto_login.py is running.")
            return jsonify({"status": "error", "message": "No Tradovate connections available"}), 500
    
    # Handle browser GET so you see a friendly page
    return (
        "<h3>🔔 Webhook endpoint is alive</h3>"
        "<p>Send a <code>POST</code> with your TradingView JSON here.</p>",
        200,
    )

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    time.sleep(1)  # Let Flask boot

    # Check if we have any Tradovate connections
    if len(controller.connections) == 0:
        print("❌ No Tradovate connections found. Make sure auto_login.py is running.")
        print("Starting server anyway, but trades cannot be executed until connections are available.")
    else:
        print(f"✅ Found {len(controller.connections)} active Tradovate connections")

    url = start_ngrok(PORT)
    if not url:
        print("🛑 Failed to start ngrok with stonkz92224.ngrok.app.")
        print("Webhook server is still accessible at http://localhost:6000/webhook")
    else:
        print("\n🚀 Webhook now accessible at:")
        print(url + "/webhook")
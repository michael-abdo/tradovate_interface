# Webhook Service Guide

This guide explains how to use the enhanced webhook service with improved resilience to system sleep/wake cycles, better error handling, and more detailed logging.

## Overview

The webhook service accepts trading signals from TradingView (or other sources) and executes them on Tradovate. The service has been enhanced to:

1. Automatically reconnect to Chrome after system sleep/wake cycles
2. Automatically restart ngrok tunnels if they disconnect
3. Provide better error handling for various payload formats
4. Include detailed logging for debugging
5. Monitor system health and recover from failures

## Starting the Webhook Service

You can start the webhook service using one of the following methods:

### Method 1: Using the launcher

```bash
python3 launchers/pinescript_webhook_launcher.py
```

### Method 2: Direct module execution

```bash
python3 -m src.pinescript_webhook
```

## Testing the Webhook

To test if your webhook service is working correctly, use the included test script:

```bash
python3 scripts/test_webhook.py
```

This script will send various test payloads to your webhook endpoint and report the results.

For a remote webhook (like ngrok), specify the URL:

```bash
python3 scripts/test_webhook.py https://stonkz92224.ngrok.app/webhook
```

## Monitoring and Restarting

### Monitoring the Webhook Service

You can monitor the webhook service health using the monitor script:

```bash
python3 scripts/monitor_webhook.py --interval 30 --notify
```

Options:
- `--interval`: Check interval in seconds (default: 60)
- `--url`: URL to the health check endpoint (default: http://localhost:6000/health)
- `--notify`: Send system notifications when status changes
- `--restart`: Path to the restart script (optional)

### Automatically Restarting the Service

If the webhook service goes down, you can automatically restart it using:

```bash
python3 scripts/monitor_webhook.py --interval 30 --notify --restart scripts/restart_webhook.sh
```

Or manually restart it:

```bash
scripts/restart_webhook.sh
```

## PineScript Integration

A sample PineScript strategy is included in `pinescript/webhook_example.pine` that demonstrates how to format webhook alerts correctly. To use this with TradingView:

1. Copy the code from `webhook_example.pine` to a new TradingView Pine Script
2. Create an alert in TradingView that triggers on your desired condition
3. Set the "Webhook URL" to your webhook endpoint (e.g., https://stonkz92224.ngrok.app/webhook)
4. Make sure "Message" is set to "{{strategy.order.alert_message}}"

## Understanding Webhook Logs

Webhook logs are stored in the `logs/` directory with timestamps. A typical log file will contain:

- Webhook request details (headers, payload)
- Connection status (Chrome, ngrok)
- Error messages if any
- Trade execution results

Example log path: `logs/webhook_20230429_123456.log`

## Troubleshooting

### Common Issues

1. **400 Bad Request Errors:**
   - Verify your payload format matches what the webhook expects
   - Check the Content-Type header (should be application/json or text/plain)
   - Look for malformed JSON in your alerts

2. **Webhook Dies After Sleep Mode:**
   - The enhanced service should automatically reconnect after waking
   - If issues persist, restart manually or use the monitor script with the restart option

3. **Chrome Connection Lost:**
   - The watchdog will automatically try to reconnect
   - Verify Chrome is running with remote debugging enabled
   - Check if auto_login.py is running

4. **Ngrok Tunnel Issues:**
   - The service will attempt to restart the ngrok tunnel automatically
   - You may need to update your ngrok authentication or domain settings

## Advanced Configuration

### Modifying the Health Check Interval

Edit the `health_check_interval` variable in `src/pinescript_webhook.py`:

```python
health_check_interval = 30  # seconds
```

### Configuring Logging

Edit the logging setup in `src/pinescript_webhook.py`:

```python
logging.basicConfig(
    level=logging.INFO,  # Change to logging.DEBUG for more details
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
```

## Contact Information

For additional support, please create an issue in the repository or contact the maintainer.
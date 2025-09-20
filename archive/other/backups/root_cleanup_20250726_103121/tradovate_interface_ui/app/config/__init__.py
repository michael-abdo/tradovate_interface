import os

# Tradovate API settings
TRADOVATE_API_URL = 'https://demo.tradovateapi.com/v1'

# Authentication details (should be moved to environment variables in production)
NAME = 'stonkz92224'
PASSWORD = '24$tonkZ24!'
APP_ID = 'Test 1'
APP_VERSION = '0.0.1'
DEVICE_ID = '96c41e70-74e5-6bb7-2057-3cd280ece582'
CID = '4398'
SEC = 'aadd1caa-ff30-4712-bc4e-1fca4c2ecad9'

# Trading settings
MAX_OPEN_POSITIONS = 1

# Port configuration
PORT = int(os.environ.get("PORT", 5001))

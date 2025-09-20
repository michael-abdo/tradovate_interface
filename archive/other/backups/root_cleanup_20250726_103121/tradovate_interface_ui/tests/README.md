# TradingView Webhook Tests

This directory contains tests for the TradingView webhook application, focusing on key features like the account phase system and size matrix.

## Python Backend Tests

The `test_account_phase_size_matrix.py` file contains unit tests for the backend Flask API, verifying that:

1. Single accounts get correct order sizes based on their phase
2. Multiple accounts with different phases each get the right size
3. The size matrix values are correctly applied
4. Sell orders also respect account phases
5. Default fallback sizes work correctly when phase sizes aren't explicitly provided

### Running the Backend Tests

To run the Python tests, use:

```bash
cd /Users/Mike/trading/tradingview_webhook
python -m unittest tests/test_account_phase_size_matrix.py
```

## JavaScript Frontend Tests

The `test_matrix_order_sequence.js` file contains tests for the frontend JavaScript logic, specifically validating:

1. Matrix values are correctly retrieved based on phase and order number
2. Account selection affects the returned order size
3. Order sequence numbers correctly determine which matrix cell to use
4. Multiple account selection behaves correctly
5. Scaling enable/disable toggle works as expected

### Running the Frontend Tests

You can run the JavaScript tests in two ways:

#### Browser Console Method

1. Open your index.html in a browser
2. Open the browser's developer tools console
3. Copy and paste the entire contents of `test_matrix_order_sequence.js` into the console
4. The tests will run automatically after a 1-second delay

#### Using Jest (optional)

If you have Node.js and Jest installed:

1. Install Jest: `npm install -g jest`
2. Create a simple Jest wrapper file that imports the test file
3. Run: `jest tests/test_matrix_order_sequence.js`

## Manual Testing Procedure

For manual verification of the matrix functionality:

1. Open the application in your browser
2. Go to the Settings panel and ensure "Use Order Scaling" is enabled
3. Configure the Size Matrix with different values for each phase and order
4. Select an account with Phase 2
5. Place an order and verify it uses the correct matrix cell value
6. Change the account to Phase 3
7. Place another order and verify it uses the right Phase 3 value
8. Place multiple orders and verify the order sequence updates correctly
9. Select multiple accounts and verify each gets the right size based on its phase

## Known Limitations

- The backend tests mock the trading service to avoid actual API calls
- The frontend tests require a DOM environment with the necessary HTML elements
- Actual HTTP requests to the trading API are not tested
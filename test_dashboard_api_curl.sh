#!/bin/bash

echo "Dashboard API Test Suite - Run when dashboard is active on port 6001"
echo "================================================================="
echo ""

# Test 1: Basic health check
echo "Test 1: Basic API Health Check"
echo "------------------------------"
echo "curl -X GET http://localhost:6001/"
echo ""

# Test 2: Problematic payload (qty=1, scale_levels=4)
echo "Test 2: Problematic Scale Order (qty=1, scale_levels=4)"
echo "--------------------------------------------------------"
echo "This should return 400 Bad Request with validation error"
echo ""
cat << 'EOF'
curl -X POST http://localhost:6001/api/trade \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NQ",
    "quantity": 1,
    "action": "Buy",
    "tick_size": 0.25,
    "account": "all",
    "enable_tp": true,
    "enable_sl": true,
    "tp_ticks": 100,
    "sl_ticks": 40,
    "scale_in_enabled": true,
    "scale_in_levels": 4,
    "scale_in_ticks": 20
  }'
EOF
echo ""

# Test 3: Valid scale payload (qty=4, scale_levels=4)
echo "Test 3: Valid Scale Order (qty=4, scale_levels=4)"
echo "--------------------------------------------------"
echo "This should succeed"
echo ""
cat << 'EOF'
curl -X POST http://localhost:6001/api/trade \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NQ",
    "quantity": 4,
    "action": "Buy",
    "tick_size": 0.25,
    "account": "all",
    "enable_tp": true,
    "enable_sl": true,
    "tp_ticks": 100,
    "sl_ticks": 40,
    "scale_in_enabled": true,
    "scale_in_levels": 4,
    "scale_in_ticks": 20
  }'
EOF
echo ""

# Test 4: Regular order without scale-in
echo "Test 4: Regular Order (no scale-in)"
echo "------------------------------------"
echo "This should always succeed"
echo ""
cat << 'EOF'
curl -X POST http://localhost:6001/api/trade \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NQ",
    "quantity": 1,
    "action": "Buy",
    "tick_size": 0.25,
    "account": "all",
    "enable_tp": true,
    "enable_sl": true,
    "tp_ticks": 100,
    "sl_ticks": 40,
    "scale_in_enabled": false
  }'
EOF
echo ""

# Test 5: Edge case - quantity equals scale levels
echo "Test 5: Edge Case (qty=2, scale_levels=2)"
echo "------------------------------------------"
echo "This should succeed (1 contract per level)"
echo ""
cat << 'EOF'
curl -X POST http://localhost:6001/api/trade \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NQ",
    "quantity": 2,
    "action": "Buy",
    "tick_size": 0.25,
    "account": "all",
    "enable_tp": true,
    "enable_sl": true,
    "tp_ticks": 100,
    "sl_ticks": 40,
    "scale_in_enabled": true,
    "scale_in_levels": 2,
    "scale_in_ticks": 20
  }'
EOF
echo ""

echo "================================================================="
echo "To execute any test, copy and run the curl command above"
echo "Make sure the dashboard is running on http://localhost:6001"
echo "================================================================="
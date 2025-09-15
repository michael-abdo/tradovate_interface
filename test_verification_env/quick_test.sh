#!/bin/bash
# Quick test runner for basic verification system checks

echo "🏃 Quick Verification System Test"
echo "================================="
echo ""

# Check if Chrome is running
echo "🔍 Checking Chrome instances..."
for port in 9223 9224 9225; do
    if curl -s "http://localhost:$port/json/list" > /dev/null; then
        echo "✅ Chrome running on port $port"
    else
        echo "❌ Chrome NOT running on port $port"
    fi
done

echo ""

# Check if test files exist
echo "📋 Checking test files..."
files_to_check=(
    "scripts/autoOrder.test.js"
    "scripts/test_end_to_end_verification.py"
    "scripts/order_execution_monitor.py"
    "test_config.json"
)

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
    fi
done

echo ""
echo "🚀 To run full test suite: python3 run_verification_tests.py"
echo "📖 For more details: cat README.md"

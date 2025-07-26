#!/bin/bash
# Quick test script for Chrome Process Watchdog

echo "Chrome Process Watchdog - Quick Test Menu"
echo "========================================"
echo ""
echo "1) Basic monitoring test (30 seconds)"
echo "2) Port protection test (manual kill required)"
echo "3) Automated crash recovery test"
echo "4) Full simulation test"
echo "5) Start_all integration test"
echo "6) Run all automated tests"
echo ""
echo "Select test (1-6) or press Enter to exit: "
read choice

case $choice in
    1)
        echo "Running basic monitoring test..."
        python3 tradovate_interface/tests/watchdog/test_basic_monitoring.py
        ;;
    2)
        echo "Running port protection test..."
        echo "NOTE: You'll need to manually kill Chrome in another terminal"
        python3 tradovate_interface/tests/watchdog/test_port_protection.py
        ;;
    3)
        echo "Running automated crash recovery test..."
        python3 tradovate_interface/tests/watchdog/test_crash_recovery.py
        ;;
    4)
        echo "Running full simulation test..."
        python3 tradovate_interface/tests/watchdog/test_full_simulation.py
        ;;
    5)
        echo "Running start_all integration test..."
        python3 tradovate_interface/tests/watchdog/test_start_all_integration.py
        ;;
    6)
        echo "Running all automated tests..."
        python3 tradovate_interface/tests/run_all_tests.py
        ;;
    *)
        echo "Exiting..."
        ;;
esac
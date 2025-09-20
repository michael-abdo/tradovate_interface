#!/bin/bash
# Final cleanup script to remove original files after verification
# Run this from the root directory: /Users/Mike/trading/algos/EOD/

echo "🧹 Final Root Directory Cleanup"
echo "================================"
echo ""

# Verify archive exists first
if [ ! -d "archive/legacy_scripts" ]; then
    echo "❌ Archive directory not found! Aborting cleanup."
    exit 1
fi

echo "📋 Files to be removed from root directory:"
echo ""

# List files that will be removed
echo "Legacy Scripts:"
echo "  - analyze_nearby_strikes.py"
echo "  - analyze_strike.py" 
echo "  - fast_run.py"
echo "  - performance_test.py"
echo "  - quick_risk_check.py"
echo "  - run_trading_system.py"
echo "  - simple_run.py"
echo "  - cleanup_old_docs.sh"
echo ""

echo "Legacy Directories:"
echo "  - coordination/ (and contents)"
echo "  - outputs/ (and contents)"
echo ""

read -p "⚠️  Are you sure you want to remove these files? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🗑️  Removing legacy files..."
    
    # Remove legacy scripts
    rm -f analyze_nearby_strikes.py
    rm -f analyze_strike.py
    rm -f fast_run.py
    rm -f performance_test.py
    rm -f quick_risk_check.py
    rm -f run_trading_system.py
    rm -f simple_run.py
    rm -f cleanup_old_docs.sh
    
    # Remove legacy directories
    rm -rf coordination/
    rm -rf outputs/
    
    echo "✅ Cleanup complete!"
    echo ""
    echo "📁 Remaining files in root:"
    ls -la
    echo ""
    echo "📦 All legacy files preserved in archive/"
    echo "    - archive/legacy_scripts/"
    echo "    - archive/legacy_coordination/" 
    echo "    - archive/legacy_outputs/"
    echo ""
    echo "🚀 Ready for new Hierarchical Pipeline Framework!"
    
else
    echo ""
    echo "❌ Cleanup cancelled. Files remain unchanged."
fi
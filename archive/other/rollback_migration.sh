#!/bin/bash
# Rollback script for tradovate_interface migration
# This script restores the original /Users/Mike/trading structure

echo "🔄 Tradovate Interface Migration Rollback Script"
echo "================================================"
echo ""
echo "This will restore the original directory structure at /Users/Mike/trading"
echo ""

# Check if backup exists
BACKUP_DIR="/tmp/trading_backup_20250801"
if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory not found at: $BACKUP_DIR"
    echo "   Cannot proceed with rollback."
    exit 1
fi

echo "✅ Found backup at: $BACKUP_DIR"
echo ""
echo "⚠️  WARNING: This will:"
echo "   - Remove /Users/Mike/tradovate_interface"
echo "   - Restore /Users/Mike/trading from backup"
echo "   - Move ngrok.yml back to project root"
echo ""
read -p "Are you sure you want to proceed? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Rollback cancelled"
    exit 0
fi

echo ""
echo "🚀 Starting rollback..."

# Step 1: Remove new directory
if [ -d "/Users/Mike/tradovate_interface" ]; then
    echo "📁 Removing /Users/Mike/tradovate_interface..."
    rm -rf /Users/Mike/tradovate_interface
fi

# Step 2: Restore from backup
echo "📂 Restoring /Users/Mike/trading from backup..."
cp -R "$BACKUP_DIR" /Users/Mike/trading

# Step 3: Restore ngrok.yml if it was moved
if [ -f ~/.ngrok2/ngrok.yml ] && [ ! -f /Users/Mike/trading/ngrok.yml ]; then
    echo "📄 Restoring ngrok.yml to project root..."
    cp ~/.ngrok2/ngrok.yml /Users/Mike/trading/ngrok.yml
fi

# Step 4: Verify restoration
if [ -d "/Users/Mike/trading" ]; then
    echo ""
    echo "✅ Rollback completed successfully!"
    echo ""
    echo "📊 Restored structure:"
    echo "   - Main directory: /Users/Mike/trading"
    echo "   - Source files in: /Users/Mike/trading/src/"
    echo "   - Config files in: /Users/Mike/trading/config/"
    echo ""
    echo "💡 Next steps:"
    echo "   1. cd /Users/Mike/trading"
    echo "   2. git status (to see any uncommitted changes)"
    echo "   3. python3 start_all.py (to test the system)"
else
    echo "❌ Rollback failed - /Users/Mike/trading was not restored"
    exit 1
fi

echo ""
echo "🎯 Rollback complete!"
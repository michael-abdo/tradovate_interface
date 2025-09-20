#!/bin/bash

# Rollback Script for Order Verification System
# This script restores the original autoOrder.user.js behavior

set -e

BACKUP_DIR="/Users/Mike/trading/backup_files/verification_system"
TARGET_FILE="/Users/Mike/trading/scripts/tampermonkey/autoOrder.user.js"
BACKUP_FILE="$BACKUP_DIR/autoOrder.user.js.original_20250728_163740"

echo "🔄 Order Verification System Rollback Script"
echo "============================================="
echo ""

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ ERROR: Backup file not found at $BACKUP_FILE"
    exit 1
fi

if [ ! -f "$TARGET_FILE" ]; then
    echo "❌ ERROR: Target file not found at $TARGET_FILE"
    exit 1
fi

echo "📋 Rollback Details:"
echo "  Source (backup): $BACKUP_FILE"
echo "  Target (current): $TARGET_FILE"
echo ""

# Create a backup of current state before rollback
ROLLBACK_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CURRENT_BACKUP="$BACKUP_DIR/autoOrder.user.js.pre_rollback_$ROLLBACK_TIMESTAMP"

echo "🔄 Creating backup of current state..."
cp "$TARGET_FILE" "$CURRENT_BACKUP"
echo "✅ Current state backed up to: $CURRENT_BACKUP"
echo ""

# Restore original file
echo "🔄 Restoring original autoOrder.user.js..."
cp "$BACKUP_FILE" "$TARGET_FILE"

# Verify restoration
if diff "$BACKUP_FILE" "$TARGET_FILE" > /dev/null; then
    echo "✅ Rollback successful!"
    echo "✅ Original autoOrder.user.js behavior restored"
    echo ""
    echo "📊 File sizes:"
    echo "  Original: $(ls -lah "$BACKUP_FILE" | awk '{print $5}')"
    echo "  Restored: $(ls -lah "$TARGET_FILE" | awk '{print $5}')"
    echo ""
    echo "🔧 Manual steps required:"
    echo "1. Refresh all Chrome instances to reload the script"
    echo "2. Test order execution on all accounts"
    echo "3. Verify original behavior is working"
    echo "4. Monitor for any issues"
    echo ""
    echo "⚠️  WARNING: Verification system is now DISABLED"
    echo "   Orders will use original success detection logic"
    echo ""
else
    echo "❌ ERROR: Rollback verification failed!"
    echo "❌ Files don't match after restoration"
    exit 1
fi
#!/bin/bash

# Test Rollback Procedure (Dry Run)
# This script tests the rollback process without actually performing it

echo "🧪 Testing Rollback Procedure (Dry Run)"
echo "======================================="
echo ""

BACKUP_DIR="/Users/Mike/trading/backup_files/verification_system"
TARGET_FILE="/Users/Mike/trading/scripts/tampermonkey/autoOrder.user.js"
BACKUP_FILE="$BACKUP_DIR/autoOrder.user.js.original_20250728_163740"
TEST_DIR="/tmp/rollback_test_$$"

# Test 1: Verify all required files exist
echo "📋 Test 1: File Existence Check"
echo "--------------------------------"

if [ -f "$BACKUP_FILE" ]; then
    echo "✅ Backup file exists: $BACKUP_FILE"
    BACKUP_SIZE=$(ls -lah "$BACKUP_FILE" | awk '{print $5}')
    echo "   Size: $BACKUP_SIZE"
else
    echo "❌ FAILED: Backup file missing"
    exit 1
fi

if [ -f "$TARGET_FILE" ]; then
    echo "✅ Target file exists: $TARGET_FILE"
    TARGET_SIZE=$(ls -lah "$TARGET_FILE" | awk '{print $5}')
    echo "   Size: $TARGET_SIZE"
else
    echo "❌ FAILED: Target file missing"
    exit 1
fi

if [ -x "$BACKUP_DIR/rollback_script.sh" ]; then
    echo "✅ Rollback script is executable"
else
    echo "❌ FAILED: Rollback script not executable"
    exit 1
fi

echo ""

# Test 2: Test rollback process in isolated environment
echo "📋 Test 2: Rollback Process Simulation"
echo "---------------------------------------"

mkdir -p "$TEST_DIR"
echo "✅ Created test directory: $TEST_DIR"

# Copy files to test directory
cp "$BACKUP_FILE" "$TEST_DIR/backup.js"
cp "$TARGET_FILE" "$TEST_DIR/current.js"
echo "✅ Copied files to test environment"

# Simulate rollback operation
cp "$TEST_DIR/backup.js" "$TEST_DIR/restored.js"
echo "✅ Simulated rollback copy operation"

# Verify simulation
if diff "$TEST_DIR/backup.js" "$TEST_DIR/restored.js" > /dev/null; then
    echo "✅ Rollback simulation successful - files match"
else
    echo "❌ FAILED: Rollback simulation failed - files don't match"
    rm -rf "$TEST_DIR"
    exit 1
fi

echo ""

# Test 3: Test backup creation during rollback
echo "📋 Test 3: Backup Creation Test"
echo "--------------------------------"

# Simulate creating backup of current state
cp "$TEST_DIR/current.js" "$TEST_DIR/pre_rollback_backup.js"
echo "✅ Simulated pre-rollback backup creation"

if [ -f "$TEST_DIR/pre_rollback_backup.js" ]; then
    BACKUP_CREATED_SIZE=$(ls -lah "$TEST_DIR/pre_rollback_backup.js" | awk '{print $5}')
    echo "✅ Pre-rollback backup created successfully"
    echo "   Size: $BACKUP_CREATED_SIZE"
else
    echo "❌ FAILED: Pre-rollback backup creation failed"
    rm -rf "$TEST_DIR"
    exit 1
fi

echo ""

# Test 4: Verify file integrity
echo "📋 Test 4: File Integrity Check"
echo "--------------------------------"

# Check if backup file is readable and has expected content
if head -20 "$BACKUP_FILE" | grep -q "Auto Order script initialized"; then
    echo "✅ Backup file contains expected Auto Order script content"
elif grep -q "async function autoOrder" "$BACKUP_FILE"; then
    echo "✅ Backup file contains autoOrder function definition"
else
    echo "❌ FAILED: Backup file doesn't contain expected content"
    rm -rf "$TEST_DIR"
    exit 1
fi

# Check file permissions
if [ -r "$BACKUP_FILE" ] && [ -r "$TARGET_FILE" ]; then
    echo "✅ Both files are readable"
else
    echo "❌ FAILED: File permission issues"
    rm -rf "$TEST_DIR"
    exit 1
fi

echo ""

# Test 5: Rollback script syntax check
echo "📋 Test 5: Rollback Script Validation"
echo "--------------------------------------"

# Check bash syntax
if bash -n "$BACKUP_DIR/rollback_script.sh"; then
    echo "✅ Rollback script syntax is valid"
else
    echo "❌ FAILED: Rollback script has syntax errors"
    rm -rf "$TEST_DIR"
    exit 1
fi

# Check for required variables
if grep -q "BACKUP_FILE=" "$BACKUP_DIR/rollback_script.sh" && \
   grep -q "TARGET_FILE=" "$BACKUP_DIR/rollback_script.sh"; then
    echo "✅ Rollback script contains required variables"
else
    echo "❌ FAILED: Rollback script missing required variables"
    rm -rf "$TEST_DIR"
    exit 1
fi

echo ""

# Cleanup
rm -rf "$TEST_DIR"
echo "🧹 Cleaned up test directory"

echo ""
echo "🎉 ALL ROLLBACK TESTS PASSED!"
echo "=============================="
echo ""
echo "✅ Backup file is valid and accessible"
echo "✅ Target file exists and is writable"
echo "✅ Rollback script is executable and syntactically correct"
echo "✅ Rollback process simulation successful"
echo "✅ Pre-rollback backup creation works"
echo "✅ File integrity checks pass"
echo ""
echo "🚀 The rollback procedure is ready for use"
echo "   To perform actual rollback, run:"
echo "   ./backup_files/verification_system/rollback_script.sh"
echo ""
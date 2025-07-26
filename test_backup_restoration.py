#!/usr/bin/env python3
"""
Test backup restoration validation for process_monitor.py
Ensures our backup can successfully restore the system
"""

import sys
import os
import shutil
import filecmp
from datetime import datetime

def test_backup_restoration():
    """Test that backup can be successfully restored"""
    print("🔄 Testing Backup Restoration Validation")
    print("=" * 50)
    
    # Paths
    original_file = "tradovate_interface/src/utils/process_monitor.py"
    backup_file = "tradovate_interface/src/utils/process_monitor.py.backup"
    test_restore_file = "tradovate_interface/src/utils/process_monitor_test_restore.py"
    
    try:
        # 1. Verify backup exists
        if not os.path.exists(backup_file):
            print(f"❌ Backup file not found: {backup_file}")
            return False
        
        print(f"✅ Backup file found: {backup_file}")
        
        # 2. Check backup file integrity
        backup_size = os.path.getsize(backup_file)
        if backup_size < 1000:  # Minimum reasonable size
            print(f"❌ Backup file too small: {backup_size} bytes")
            return False
        
        print(f"✅ Backup file size reasonable: {backup_size} bytes")
        
        # 3. Test restoration by copying backup to test location
        shutil.copy2(backup_file, test_restore_file)
        print(f"✅ Backup copied to test location: {test_restore_file}")
        
        # 4. Verify restored file can be imported
        sys.path.insert(0, os.path.dirname(test_restore_file))
        try:
            # Try to import from the restored file
            import importlib.util
            spec = importlib.util.spec_from_file_location("test_process_monitor", test_restore_file)
            test_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_module)
            
            # Check critical classes exist
            if hasattr(test_module, 'ChromeProcessMonitor'):
                print("✅ ChromeProcessMonitor class found in restored backup")
            else:
                print("❌ ChromeProcessMonitor class missing in restored backup")
                return False
            
            if hasattr(test_module, 'ProcessState'):
                print("✅ ProcessState enum found in restored backup")
            else:
                print("❌ ProcessState enum missing in restored backup")
                return False
            
            # Try to instantiate the monitor from backup
            monitor = test_module.ChromeProcessMonitor()
            print("✅ ChromeProcessMonitor can be instantiated from backup")
            
            # Test basic functionality
            if hasattr(monitor, 'register_process'):
                print("✅ Basic methods available in restored backup")
            else:
                print("❌ Basic methods missing in restored backup")
                return False
            
        except Exception as e:
            print(f"❌ Error importing restored backup: {e}")
            return False
        
        # 5. Compare backup with current file structure (basic validation)
        try:
            with open(backup_file, 'r') as f:
                backup_content = f.read()
            
            # Check for critical components
            critical_components = [
                'class ChromeProcessMonitor',
                'def register_process',
                'def start_monitoring',
                'def stop_monitoring',
                'class ProcessState',
                'def _monitoring_loop'
            ]
            
            missing_components = []
            for component in critical_components:
                if component not in backup_content:
                    missing_components.append(component)
            
            if missing_components:
                print(f"❌ Critical components missing from backup: {missing_components}")
                return False
            else:
                print("✅ All critical components found in backup")
            
        except Exception as e:
            print(f"❌ Error analyzing backup content: {e}")
            return False
        
        # 6. Test backup metadata
        backup_mtime = os.path.getmtime(backup_file)
        backup_date = datetime.fromtimestamp(backup_mtime)
        
        # Check if backup is reasonably recent (not older than the project)
        if backup_date.year < 2024:
            print(f"⚠️  Backup appears very old: {backup_date}")
        else:
            print(f"✅ Backup timestamp reasonable: {backup_date}")
        
        print("\n✅ BACKUP RESTORATION VALIDATION SUCCESSFUL")
        print("The backup can be successfully restored and used")
        
        return True
        
    except Exception as e:
        print(f"❌ Backup restoration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup test restore file
        if os.path.exists(test_restore_file):
            os.remove(test_restore_file)
            print(f"🧹 Cleaned up test file: {test_restore_file}")

def create_additional_backups():
    """Create additional backups for related files"""
    print("\n🔄 Creating Additional System Backups")
    print("=" * 50)
    
    files_to_backup = [
        "tradovate_interface/config/process_monitor.json",
        "src/auto_login.py",
        "src/dashboard.py"
    ]
    
    backup_count = 0
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup_{timestamp}"
            try:
                shutil.copy2(file_path, backup_path)
                print(f"✅ Backed up: {file_path} -> {backup_path}")
                backup_count += 1
            except Exception as e:
                print(f"⚠️  Failed to backup {file_path}: {e}")
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"✅ Created {backup_count} additional backups")
    return backup_count > 0

def main():
    """Main backup validation test"""
    print("🔍 Comprehensive Backup Validation Test")
    print("=" * 60)
    
    # Test main backup restoration
    restoration_success = test_backup_restoration()
    
    # Create additional backups
    additional_backups = create_additional_backups()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 BACKUP VALIDATION SUMMARY")
    print("=" * 60)
    
    if restoration_success:
        print("✅ Main backup restoration: PASSED")
    else:
        print("❌ Main backup restoration: FAILED")
    
    if additional_backups:
        print("✅ Additional backups created: PASSED")
    else:
        print("⚠️  Additional backups created: PARTIAL")
    
    overall_success = restoration_success and additional_backups
    
    if overall_success:
        print("\n🎉 BACKUP VALIDATION COMPLETE AND SUCCESSFUL")
        print("System can be safely restored from backups")
        return 0
    else:
        print("\n⚠️  BACKUP VALIDATION ISSUES DETECTED")
        print("Review backup strategy and fix identified issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())
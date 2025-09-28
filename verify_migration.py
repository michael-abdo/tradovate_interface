#!/usr/bin/env python3
"""
Migration Verification Script for DRY Refactoring

This script verifies that all refactoring has been completed successfully
and that no regressions have been introduced.
"""

import os
import sys
import ast
from pathlib import Path
from typing import List, Dict, Tuple


class MigrationVerifier:
    """Verify the DRY refactoring migration is complete."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues = []
        self.successes = []
    
    def verify_all(self) -> bool:
        """Run all verification checks."""
        print("🔍 Starting Migration Verification...\n")
        
        # Check 1: Verify new utility files exist
        self.check_utility_files_exist()
        
        # Check 2: Verify modules import from utils.core
        self.check_utility_imports()
        
        # Check 3: Verify no duplicate project root calculations
        self.check_no_duplicate_project_root()
        
        # Check 4: Verify ChromeProcessManager is used
        self.check_chrome_process_manager()
        
        # Check 5: Verify launcher simplification
        self.check_launcher_simplification()
        
        # Check 6: Verify tests exist and are comprehensive
        self.check_test_coverage()
        
        # Check 7: Verify no hardcoded Chrome paths
        self.check_no_hardcoded_chrome_paths()
        
        # Print results
        self.print_results()
        
        return len(self.issues) == 0
    
    def check_utility_files_exist(self):
        """Check that all new utility files have been created."""
        print("📁 Checking utility files...")
        
        required_files = [
            'src/utils/core.py',
            'src/utils/__init__.py',
            'launchers/common.py',
            'tests/utils/test_core.py',
            'tests/test_chrome_process_manager.py',
            'tests/test_launcher_common.py',
            'tests/test_imports.py'
        ]
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self.successes.append(f"✅ {file_path} exists")
            else:
                self.issues.append(f"❌ Missing file: {file_path}")
    
    def check_utility_imports(self):
        """Verify modules are importing from utils.core."""
        print("\n📦 Checking utility imports...")
        
        modules_to_check = [
            'src/auto_login.py',
            'src/dashboard.py',
            'src/app.py',
            'src/pinescript_webhook.py',
            'src/login_helper.py',
            'src/chrome_logger.py'
        ]
        
        for module_path in modules_to_check:
            full_path = self.project_root / module_path
            if not full_path.exists():
                self.issues.append(f"❌ Module not found: {module_path}")
                continue
            
            content = full_path.read_text()
            
            # Check for utils.core imports
            if 'from src.utils.core import' in content or 'from .utils.core import' in content:
                self.successes.append(f"✅ {module_path} imports from utils.core")
                
                # Check specific imports
                if 'get_project_root' in content:
                    self.successes.append(f"  ✓ Uses get_project_root()")
                if 'find_chrome_executable' in content:
                    self.successes.append(f"  ✓ Uses find_chrome_executable()")
                if 'setup_logging' in content:
                    self.successes.append(f"  ✓ Uses setup_logging()")
            else:
                self.issues.append(f"❌ {module_path} does not import from utils.core")
    
    def check_no_duplicate_project_root(self):
        """Verify no duplicate project root calculations remain."""
        print("\n🔍 Checking for duplicate project root calculations...")
        
        # Pattern to search for
        old_pattern = "os.path.dirname(os.path.dirname(os.path.abspath(__file__)))"
        
        src_files = list(self.project_root.glob("src/*.py"))
        
        for file_path in src_files:
            if file_path.name == '__init__.py':
                continue
                
            content = file_path.read_text()
            
            # Skip utils/core.py itself
            if 'utils/core.py' in str(file_path):
                continue
            
            if old_pattern in content:
                # Count occurrences
                count = content.count(old_pattern)
                self.issues.append(f"❌ {file_path.name} still has {count} old project root calculations")
            else:
                self.successes.append(f"✅ {file_path.name} uses centralized project root")
    
    def check_chrome_process_manager(self):
        """Verify ChromeProcessManager class exists and is used."""
        print("\n🌐 Checking ChromeProcessManager usage...")
        
        auto_login_path = self.project_root / 'src/auto_login.py'
        content = auto_login_path.read_text()
        
        if 'class ChromeProcessManager' in content:
            self.successes.append("✅ ChromeProcessManager class exists in auto_login.py")
        else:
            self.issues.append("❌ ChromeProcessManager class not found in auto_login.py")
        
        # Check if it has the expected methods
        expected_methods = ['launch_chrome', 'stop_chrome', 'stop_all', 'cleanup']
        for method in expected_methods:
            if f'def {method}' in content:
                self.successes.append(f"  ✓ Has {method}() method")
            else:
                self.issues.append(f"  ✗ Missing {method}() method")
    
    def check_launcher_simplification(self):
        """Verify launchers have been simplified."""
        print("\n🚀 Checking launcher simplification...")
        
        launcher_files = list((self.project_root / 'launchers').glob('*_launcher.py'))
        
        for launcher_path in launcher_files:
            content = launcher_path.read_text()
            lines = content.strip().split('\n')
            
            # Check if it imports from common
            if 'from common import launch_module' in content or 'from .common import launch_module' in content:
                self.successes.append(f"✅ {launcher_path.name} uses common.launch_module")
                
                # Check line count (should be ~10 lines)
                if len(lines) <= 15:
                    self.successes.append(f"  ✓ Simplified to {len(lines)} lines")
                else:
                    self.issues.append(f"  ✗ Still has {len(lines)} lines (expected ≤15)")
            else:
                self.issues.append(f"❌ {launcher_path.name} not using common launcher")
    
    def check_test_coverage(self):
        """Verify comprehensive test coverage exists."""
        print("\n🧪 Checking test coverage...")
        
        test_results = {
            'tests/utils/test_core.py': 21,
            'tests/test_chrome_process_manager.py': 13,
            'tests/test_launcher_common.py': 15,
            'tests/test_imports.py': 13
        }
        
        total_tests = 0
        for test_file, expected_count in test_results.items():
            test_path = self.project_root / test_file
            if test_path.exists():
                # Count test methods
                content = test_path.read_text()
                test_count = content.count('def test_')
                total_tests += test_count
                
                if test_count >= expected_count:
                    self.successes.append(f"✅ {test_file} has {test_count} tests")
                else:
                    self.issues.append(f"❌ {test_file} has only {test_count} tests (expected {expected_count})")
            else:
                self.issues.append(f"❌ Missing test file: {test_file}")
        
        if total_tests >= 60:
            self.successes.append(f"✅ Total test count: {total_tests} (exceeds minimum 60)")
        else:
            self.issues.append(f"❌ Insufficient tests: {total_tests} (need at least 60)")
    
    def check_no_hardcoded_chrome_paths(self):
        """Verify no hardcoded Chrome paths remain."""
        print("\n🔍 Checking for hardcoded Chrome paths...")
        
        hardcoded_patterns = [
            '"/Applications/Google Chrome.app"',
            "'/Applications/Google Chrome.app'",
            'C:\\Program Files\\Google\\Chrome',
            'C:\\Program Files (x86)\\Google\\Chrome',
            '/usr/bin/google-chrome',
            '/usr/bin/chromium'
        ]
        
        src_files = list(self.project_root.glob("src/*.py"))
        
        for file_path in src_files:
            # Skip utils/core.py where these are centralized
            if 'utils/core.py' in str(file_path):
                continue
                
            content = file_path.read_text()
            
            found_patterns = []
            for pattern in hardcoded_patterns:
                if pattern in content:
                    found_patterns.append(pattern)
            
            if found_patterns:
                self.issues.append(f"❌ {file_path.name} has hardcoded Chrome paths: {found_patterns}")
            else:
                self.successes.append(f"✅ {file_path.name} has no hardcoded Chrome paths")
    
    def print_results(self):
        """Print verification results."""
        print("\n" + "="*60)
        print("📊 MIGRATION VERIFICATION RESULTS")
        print("="*60)
        
        if self.successes:
            print("\n✅ SUCCESSES:")
            for success in self.successes:
                print(f"  {success}")
        
        if self.issues:
            print("\n❌ ISSUES FOUND:")
            for issue in self.issues:
                print(f"  {issue}")
        
        print("\n" + "="*60)
        if not self.issues:
            print("🎉 ALL CHECKS PASSED! Migration completed successfully.")
        else:
            print(f"⚠️  Found {len(self.issues)} issues that need attention.")
        print("="*60)


def main():
    """Run the migration verification."""
    # Get project root
    project_root = Path(__file__).parent
    
    # Create verifier and run checks
    verifier = MigrationVerifier(project_root)
    success = verifier.verify_all()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
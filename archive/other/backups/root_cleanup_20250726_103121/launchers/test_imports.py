#!/usr/bin/env python3
"""
Test script to verify that all module imports are working correctly.
Run this to check if the Python path is set up properly.
"""

import os
import sys

# Add the project root to the path so we can import from src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_imports():
    """Test all critical module imports"""
    import_errors = []
    import_successes = []
    
    # List of modules to test
    modules_to_test = [
        # Core modules
        "src.app",
        "src.auto_login",
        "src.login_helper",
        "src.dashboard",
        "src.pinescript_webhook",
        "src.chrome_logger",
        
        # Utils
        "utils.fix_imports",
        
        # Examples
        "src.examples.example_using_login",
        
        # Sub-imports to test
        "src.app.TradovateController",
        "src.dashboard.run_flask_dashboard",
        "src.pinescript_webhook.run_flask",
        "src.login_helper.login_to_existing_chrome",
    ]
    
    # Try importing each module
    for module_name in modules_to_test:
        try:
            if "." in module_name and not module_name.startswith("src.") and not module_name.startswith("utils."):
                # For imports like module.Class
                parts = module_name.split(".")
                module_path, item_name = ".".join(parts[:-1]), parts[-1]
                
                module = __import__(module_path, fromlist=[item_name])
                item = getattr(module, item_name)
                import_successes.append(f"✅ Successfully imported {item_name} from {module_path}")
            else:
                # For regular imports
                __import__(module_name)
                import_successes.append(f"✅ Successfully imported {module_name}")
        except ImportError as e:
            import_errors.append(f"❌ Failed to import {module_name}: {e}")
    
    # Print results
    print("\n=== Import Test Results ===\n")
    
    if import_successes:
        print("Successful imports:")
        for success in import_successes:
            print(f"  {success}")
    
    if import_errors:
        print("\nFailed imports:")
        for error in import_errors:
            print(f"  {error}")
        
        print("\nPossible solutions:")
        print("1. Make sure you're running this script from the project root directory")
        print("2. Use the main.py entry point: python main.py <component>")
        print("3. Use the launcher scripts in the launchers directory")
        print("4. Add the project root to your PYTHONPATH environment variable")
        print("5. See docs/TROUBLESHOOTING.md for more information")
    else:
        print("\nAll imports successful! Your Python path is set up correctly.")
    
    return len(import_errors) == 0

if __name__ == "__main__":
    print("Testing module imports...\n")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
    print(f"Project root: {project_root}")
    print(f"Python path: {sys.path[0]}")
    
    success = test_imports()
    
    if not success:
        sys.exit(1)
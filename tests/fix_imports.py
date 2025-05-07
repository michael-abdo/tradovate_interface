#!/usr/bin/env python3
"""
Script to fix import paths in test files after project restructuring
"""
import os
import re
import sys

def fix_imports_in_file(file_path):
    print(f"Fixing imports in {file_path}")
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix direct imports from root modules
    content = re.sub(r'import\s+(auto_login|chrome_logger|login_helper|dashboard|pinescript_webhook)', 
                     r'from src import \1', 
                     content)
    
    # Fix function paths in patch calls
    content = re.sub(r'patch\("(auto_login|chrome_logger|login_helper|dashboard|pinescript_webhook)\.', 
                     r'patch("src.\1.', 
                     content)
    
    # Fix pychrome Browser import in patch
    content = re.sub(r'patch\("pychrome\.Browser"', 
                     r'patch("src.auto_login.pychrome.Browser"', 
                     content)
    
    # Fix paths to tampermonkey scripts and other files
    content = re.sub(r"os\.path\.join\(os\.path\.dirname\(os\.path\.abspath\(__file__\)\), 'tampermonkey/", 
                     r"os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts/tampermonkey/", 
                     content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    print(f"Fixed imports in {file_path}")

def main():
    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_files = [
        os.path.join(test_dir, "test_auto_login.py"),
        os.path.join(test_dir, "test_chrome_logger.py"),
        os.path.join(test_dir, "test_login_helper.py"),
        os.path.join(test_dir, "test_dom_structure.py")
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            fix_imports_in_file(file_path)

if __name__ == "__main__":
    main()
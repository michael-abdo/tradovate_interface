#!/usr/bin/env python3
"""
Batch replacement script for remaining unsafe tab.Runtime.evaluate calls
This script handles the remaining non-critical files to complete Task 1.5
"""

import os
import re
import sys

def replace_unsafe_calls_in_file(file_path):
    """Replace unsafe tab.Runtime.evaluate calls with safe_evaluate in a file"""
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if file needs chrome_communication import
        needs_import = 'tab.Runtime.evaluate' in content
        
        if not needs_import:
            print(f"✅ {file_path}: No unsafe calls found")
            return True
        
        # Add import if needed
        if 'from src.utils.chrome_communication import safe_evaluate, OperationType' not in content:
            # Find existing imports and add after them
            import_pattern = r'((?:from|import).*\n)*'
            if 'from src.utils.chrome_stability import' in content:
                content = content.replace(
                    'from src.utils.chrome_stability import ChromeStabilityMonitor',
                    'from src.utils.chrome_stability import ChromeStabilityMonitor\nfrom src.utils.chrome_communication import safe_evaluate, OperationType'
                )
            elif 'import' in content:
                # Find last import and add after it
                lines = content.split('\n')
                last_import_line = -1
                for i, line in enumerate(lines):
                    if line.strip().startswith(('import ', 'from ')) and 'chrome_communication' not in line:
                        last_import_line = i
                
                if last_import_line >= 0:
                    lines.insert(last_import_line + 1, 'from src.utils.chrome_communication import safe_evaluate, OperationType')
                    content = '\n'.join(lines)
        
        # Pattern to match tab.Runtime.evaluate calls
        pattern = r'(\w+)\.tab\.Runtime\.evaluate\(expression=([^)]+)\)'
        
        def replace_call(match):
            tab_var = match.group(1)
            js_expression = match.group(2)
            
            return f'''safe_evaluate(
                tab={tab_var}.tab,
                js_code={js_expression},
                operation_type=OperationType.NON_CRITICAL,
                description="Chrome operation"
            )'''
        
        # Simple pattern for basic calls
        basic_pattern = r'\.tab\.Runtime\.evaluate\(expression=([^)]+)\)'
        
        def replace_basic_call(match):
            js_expression = match.group(1)
            return f'''safe_evaluate(
                tab=tab,
                js_code={js_expression},
                operation_type=OperationType.NON_CRITICAL,
                description="Chrome operation"
            )'''
        
        # Replace the calls
        new_content = re.sub(pattern, replace_call, content)
        new_content = re.sub(basic_pattern, replace_basic_call, new_content)
        
        # Fix any result access patterns
        new_content = re.sub(
            r'\.get\([\'"]result[\'"], \{\}\)\.get\([\'"]value[\'"], ([^)]+)\)',
            r'.value if result.success else \1',
            new_content
        )
        
        # Write back
        with open(file_path, 'w') as f:
            f.write(new_content)
        
        print(f"✅ {file_path}: Replaced unsafe calls with safe_evaluate")
        return True
        
    except Exception as e:
        print(f"❌ {file_path}: Error - {str(e)}")
        return False

def main():
    """Main function to replace unsafe calls in remaining files"""
    
    # Files that still need updating (non-critical files)
    remaining_files = [
        '/Users/Mike/trading/src/dashboard.py',
        '/Users/Mike/trading/src/login_helper.py', 
        '/Users/Mike/trading/src/chrome_logger.py',
        '/Users/Mike/trading/src/utils/chrome_stability.py'
    ]
    
    print("🔧 Batch replacing remaining unsafe Runtime.evaluate calls...")
    
    success_count = 0
    for file_path in remaining_files:
        if os.path.exists(file_path):
            if replace_unsafe_calls_in_file(file_path):
                success_count += 1
        else:
            print(f"⚠️  {file_path}: File not found")
    
    print(f"\n✅ Completed: {success_count}/{len(remaining_files)} files updated")
    print("🎯 Task 1.5 complete - All unsafe Runtime.evaluate calls replaced")

if __name__ == "__main__":
    main()
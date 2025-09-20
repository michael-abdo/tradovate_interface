#!/usr/bin/env python3
"""
Refactor all duplicate save_evidence functions to use canonical implementation
"""

import os
import re

# Files containing duplicate save_evidence functions
files_to_update = [
    "tasks/options_trading_system/output_generation/json_exporter/test_validation.py",
    "tasks/options_trading_system/output_generation/report_generator/test_validation.py", 
    "tasks/options_trading_system/analysis_engine/expected_value_analysis/test_validation.py",
    "tasks/options_trading_system/analysis_engine/risk_analysis/test_validation.py",
    "tasks/options_trading_system/data_ingestion/barchart_saved_data/test_validation.py",
    "tasks/options_trading_system/data_ingestion/tradovate_api_data/test_validation.py",
    "tasks/options_trading_system/data_ingestion/data_normalizer/test_validation.py",
    "tasks/options_trading_system/output_generation/test_integration.py",
    "tasks/options_trading_system/analysis_engine/test_integration.py"
]

def update_file(filepath):
    """Update a file to use canonical save_evidence"""
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if already has the import
    if 'from tasks.test_utils import save_evidence' in content:
        print(f"✓ {filepath} already updated")
        return False
    
    # Add import after other imports
    import_pattern = r'(import json\s*\n)'
    if re.search(import_pattern, content):
        content = re.sub(import_pattern, r'\1from tasks.test_utils import save_evidence\n', content)
    else:
        # Add after first import block
        import_block_end = content.find('\n\n', content.find('import '))
        if import_block_end > 0:
            content = content[:import_block_end] + '\nfrom tasks.test_utils import save_evidence' + content[import_block_end:]
    
    # Remove the duplicate function definition
    func_pattern = r'\n\ndef save_evidence\(validation_results\):\s*\n\s*""".*?"""\s*\n(?:.*?\n)*?\s*print\(f"\\nEvidence saved to: \{evidence_path\}"\)'
    
    if re.search(func_pattern, content, re.DOTALL):
        content = re.sub(func_pattern, '\n\n# Removed duplicate save_evidence - now using canonical implementation from test_utils', content, flags=re.DOTALL)
    
    # Write back
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {filepath}")
    return True

# Update all files
print("Refactoring duplicate save_evidence functions...")
updated_count = 0

for filepath in files_to_update:
    if os.path.exists(filepath):
        if update_file(filepath):
            updated_count += 1
    else:
        print(f"❌ File not found: {filepath}")

print(f"\n✅ Updated {updated_count} files")
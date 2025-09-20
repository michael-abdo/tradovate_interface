#!/usr/bin/env python3
"""
Fix imports for test_utils in all files
"""

import os

files_to_fix = [
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

for filepath in files_to_fix:
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        continue
        
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Find the line with save_evidence import
    for i, line in enumerate(lines):
        if 'from tasks.test_utils import save_evidence' in line and i > 0:
            # Check if previous line has sys.path.insert
            if 'sys.path.insert' not in lines[i-1]:
                # Insert the proper path setup before the import
                depth = filepath.count('/') - 1  # -1 because we're counting from 'tasks'
                parent_calls = 'os.path.dirname(' * depth + 'os.path.abspath(__file__)' + ')' * depth
                lines[i] = f"sys.path.insert(0, os.path.dirname({parent_calls}))\n{line}"
                
                with open(filepath, 'w') as f:
                    f.writelines(lines)
                print(f"✅ Fixed import in {filepath}")
                break
    else:
        print(f"✓ {filepath} already OK")

print("\nDone!")
# Archive Manifest

This directory contains files and directories that were moved during the root cleanup process on $(date).

## Archived Items:

- **temp/**: Temporary files directory
- **test_report.json**: Old test report file
- **pre_implementation_check.py**: Pre-implementation validation script
- **launchers/**: Directory containing various launcher scripts
- **test_summary_20250725_212744.txt**: Old test summary
- **start_all_backup.py**: Backup of start_all.py
- **test_logs/**: Old test log files

## Reason for Archival:
These files were either:
1. Duplicate functionality now handled by organized structure
2. Old/obsolete files no longer needed
3. Temporary files that accumulated over time
4. Backup files that are redundant

## Recovery:
If any of these files are needed, they can be restored from this archive.

## Major Archive Items:

- **tradovate_interface/**: Complete separate git repository with older versions of the codebase
  - Reason: Root directory contains more current versions with watchdog features
  - Contains: Duplicate src/, tests/, docs/, scripts/ directories with older code
  - Status: Separate git repository maintained for historical reference

- **tradovate_interface_ui/**: Related UI component project
  - Reason: Part of the tradovate interface ecosystem but separate from main trading system
  - Status: Archived for potential future reference


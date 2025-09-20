#!/usr/bin/env python3
"""
Automated migration script to make tradovate_interface the new root
"""
import os
import re
import sys
import shutil
from pathlib import Path

class RootMigrator:
    """Migration tool for restructuring to tradovate_interface as root"""
    
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.changes = []
        self.errors = []
        
    def log_change(self, message):
        """Log a change that will be made"""
        self.changes.append(message)
        print(f"{'[DRY-RUN] ' if self.dry_run else '[EXECUTE] '}{message}")
        
    def log_error(self, message):
        """Log an error"""
        self.errors.append(message)
        print(f"ERROR: {message}")
        
    def update_python_imports(self, file_path):
        """Update Python imports from 'src.' to direct imports"""
        try:
            with open(file_path, 'r') as f:
                original = f.read()
                
            modified = original
            
            # Update common import patterns
            modified = re.sub(r'from src\.', 'from ', modified)
            modified = re.sub(r'import app\.', 'import ', modified)
            modified = re.sub(r'import app\b', 'import app', modified)
            
            if modified != original:
                self.log_change(f"Updated Python imports in {file_path}")
                if not self.dry_run:
                    with open(file_path, 'w') as f:
                        f.write(modified)
                return True
            return False
            
        except Exception as e:
            self.log_error(f"Error updating imports in {file_path}: {e}")
            return False
            
    def update_absolute_paths(self, file_path):
        """Update absolute paths from /Users/Mike/tradovate_interface to /Users/Mike/tradovate_interface"""
        try:
            with open(file_path, 'r') as f:
                original = f.read()
                
            modified = original
            
            # Update absolute paths
            modified = modified.replace('/Users/Mike/tradovate_interface', '/Users/Mike/tradovate_interface')
            
            if modified != original:
                self.log_change(f"Updated absolute paths in {file_path}")
                if not self.dry_run:
                    with open(file_path, 'w') as f:
                        f.write(modified)
                return True
            return False
            
        except Exception as e:
            self.log_error(f"Error updating paths in {file_path}: {e}")
            return False
            
    def move_src_contents_to_root(self):
        """Move contents of src/ directory to root level"""
        src_path = Path('src')
        if not src_path.exists():
            self.log_change("No src/ directory found, skipping file moves")
            return
            
        self.log_change("Moving src/ directory contents to root level")
        
        if not self.dry_run:
            # Move all files and directories from src/ to root
            for item in src_path.iterdir():
                dest = Path(item.name)
                if dest.exists():
                    if dest.is_dir() and item.is_dir():
                        # Merge directories by moving contents
                        self.log_change(f"Merging directory {item} into existing {dest}")
                        for sub_item in item.iterdir():
                            sub_dest = dest / sub_item.name
                            if sub_dest.exists():
                                self.log_error(f"Cannot merge {sub_item} - {sub_dest} already exists")
                                continue
                            shutil.move(str(sub_item), str(sub_dest))
                            self.log_change(f"Merged {sub_item} → {sub_dest}")
                        # Remove empty source directory
                        if not any(item.iterdir()):
                            item.rmdir()
                            self.log_change(f"Removed empty directory {item}")
                    else:
                        self.log_error(f"Destination {dest} already exists, skipping {item}")
                        continue
                else:
                    shutil.move(str(item), str(dest))
                    self.log_change(f"Moved {item} → {dest}")
            
            # Remove empty src directory
            if not any(src_path.iterdir()):
                src_path.rmdir()
                self.log_change("Removed empty src/ directory")
        else:
            # Just log what would be moved
            for item in src_path.iterdir():
                dest = Path(item.name)
                self.log_change(f"Would move {item} → {dest}")
            self.log_change("Would remove empty src/ directory")

    def run(self):
        """Run the migration process"""
        print(f"Starting migration process...")
        
        # Skip directories that shouldn't be processed
        skip_dirs = ['worktree', 'organized', '__pycache__', '.git', 'logs', 
                    'backups', 'backup_files', 'test_verification_env']
        
        # Find all Python files
        python_files = []
        for py_file in Path('.').glob('**/*.py'):
            if any(skip in str(py_file) for skip in skip_dirs):
                continue
            python_files.append(py_file)
            
        print(f"Found {len(python_files)} Python files to process")
        
        # Process Python files
        for py_file in python_files:
            self.update_python_imports(py_file)
            self.update_absolute_paths(py_file)
            
        # Find and process shell scripts
        shell_files = []
        for sh_file in Path('.').glob('**/*.sh'):
            if any(skip in str(sh_file) for skip in skip_dirs):
                continue
            shell_files.append(sh_file)
            
        print(f"Found {len(shell_files)} shell scripts to process")
        
        # Process shell scripts
        for sh_file in shell_files:
            self.update_absolute_paths(sh_file)
            
        # Move src/ contents to root level (final step)
        self.move_src_contents_to_root()
            
        # Summary
        print(f"\nMigration {'simulation' if self.dry_run else 'execution'} complete!")
        print(f"Total changes: {len(self.changes)}")
        print(f"Total errors: {len(self.errors)}")
        
        if self.errors:
            print("\nErrors encountered:")
            for error in self.errors:
                print(f"  - {error}")
                
        return len(self.errors) == 0

if __name__ == "__main__":
    dry_run = '--dry-run' in sys.argv or len(sys.argv) == 1  # Default to dry-run
    
    # Check for directory argument
    target_dir = None
    for arg in sys.argv:
        if arg.startswith('--dir='):
            target_dir = arg.split('=', 1)[1]
            break
    
    if target_dir:
        print(f"Changing to directory: {target_dir}")
        os.chdir(target_dir)
    
    migrator = RootMigrator(dry_run=dry_run)
    
    print(f"Migration script running in {'DRY-RUN' if dry_run else 'EXECUTE'} mode")
    print(f"Working directory: {os.getcwd()}")
    print("Use --execute to actually perform changes")
    print("Use --dir=/path/to/directory to specify target directory")
    print("-" * 50)
    
    # Run the migration
    success = migrator.run()
    
    if success:
        print("\n✅ Migration completed successfully!")
    else:
        print("\n❌ Migration completed with errors!")
        sys.exit(1)
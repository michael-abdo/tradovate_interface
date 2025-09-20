# Making tradovate_interface the New Root: Migration Plan

## Difficulty Assessment: **MODERATE** (3/5)

### Why It's Not Too Difficult:
1. **Limited scope**: Only ~40-47 files need updates
2. **Mechanical changes**: Most are simple find-and-replace operations
3. **No logic changes**: Just import paths and file references
4. **Git safety net**: Can always revert if something goes wrong

### Why It Requires Care:
1. **Active system**: This is a live trading system
2. **Multiple entry points**: start_all.py, main.py, various scripts
3. **Shell scripts**: Path updates in bash scripts can be error-prone
4. **Testing critical**: Must verify all imports work before deploying

## Safe Migration Strategy

### Phase 1: Preparation (Low Risk)
```bash
# 1. Create a new branch for the migration
git checkout -b migrate-to-tradovate-interface-root

# 2. Create the migration script
cat > migrate_to_new_root.py << 'EOF'
#!/usr/bin/env python3
"""
Automated migration script to make tradovate_interface the new root
"""
import os
import re
import shutil
from pathlib import Path

def update_python_imports(file_path):
    """Update Python imports from 'src.' to direct imports"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Update imports
    content = re.sub(r'from src\.', 'from ', content)
    content = re.sub(r'import src\.', 'import ', content)
    
    with open(file_path, 'w') as f:
        f.write(content)

def update_absolute_paths(file_path):
    """Update absolute paths from /Users/Mike/trading to /Users/Mike/tradovate_interface"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    content = content.replace('/Users/Mike/trading', '/Users/Mike/tradovate_interface')
    
    with open(file_path, 'w') as f:
        f.write(content)

# Main migration logic here...
EOF

# 3. Create a backup
cp -r /Users/Mike/trading /Users/Mike/trading_backup_$(date +%Y%m%d_%H%M%S)
```

### Phase 2: Test Migration (Medium Risk)
```bash
# 1. Create test directory structure
mkdir -p /tmp/tradovate_interface_test
cp -r /Users/Mike/trading/* /tmp/tradovate_interface_test/

# 2. Run migration on test copy
cd /tmp/tradovate_interface_test
python3 migrate_to_new_root.py

# 3. Test critical functions
python3 -m pytest tests/  # Run test suite
python3 main.py --help    # Verify CLI works
```

### Phase 3: Staged Migration (Controlled Risk)

#### Step 1: Create New Structure
```bash
# Create tradovate_interface as new root
mkdir -p /Users/Mike/tradovate_interface
cd /Users/Mike/trading

# Move everything except .git
rsync -av --exclude='.git' --exclude='worktree' --exclude='organized' \
  --exclude='*.log' --exclude='__pycache__' --exclude='.DS_Store' \
  ./ /Users/Mike/tradovate_interface/
```

#### Step 2: Update Import Paths
```python
# Files to update (from src.* to direct imports):
src/app.py
src/auto_login.py
src/dashboard.py
src/utils/*.py
main.py
tests/*.py
```

#### Step 3: Update Shell Scripts
```bash
# Update these scripts:
scripts/save_ngrok_url.sh
scripts/start_dashboard_with_ngrok.sh
scripts/restart_webhook.sh
start_all.py (project_root variable)
```

#### Step 4: Update Configuration
```bash
# Move ngrok.yml to standard location
mv ngrok.yml ~/.ngrok2/ngrok.yml

# Update current_ngrok_url.txt location in scripts
# Consider moving to config/runtime/current_ngrok_url.txt
```

### Phase 4: Validation & Rollback Plan

#### Validation Steps:
1. **Import Test**: `python3 -c "import app, auto_login, dashboard"`
2. **Unit Tests**: `python3 -m pytest tests/`
3. **Start Test**: `python3 start_all.py --dry-run`
4. **Component Test**: Test each component individually
5. **Full System Test**: Run complete trading system

#### Rollback Plan:
```bash
# If anything goes wrong:
cd /Users/Mike
mv tradovate_interface tradovate_interface_failed
mv trading_backup_[timestamp] trading

# Or if using git:
git checkout master
git branch -D migrate-to-tradovate-interface-root
```

## Automated Migration Script

```python
#!/usr/bin/env python3
"""migrate_to_tradovate_interface_root.py"""

import os
import re
import sys
from pathlib import Path

class RootMigrator:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.changes = []
        
    def migrate_python_imports(self, file_path):
        """Update Python imports"""
        with open(file_path, 'r') as f:
            original = f.read()
            
        modified = original
        modified = re.sub(r'from src\.', 'from ', modified)
        modified = re.sub(r'import src\.', 'import ', modified)
        modified = re.sub(r'import src\b', 'import app', modified)
        
        if modified != original:
            self.changes.append(f"Updated imports in {file_path}")
            if not self.dry_run:
                with open(file_path, 'w') as f:
                    f.write(modified)
                    
    def migrate_paths(self, file_path):
        """Update absolute paths"""
        with open(file_path, 'r') as f:
            original = f.read()
            
        modified = original.replace(
            '/Users/Mike/trading',
            '/Users/Mike/tradovate_interface'
        )
        
        if modified != original:
            self.changes.append(f"Updated paths in {file_path}")
            if not self.dry_run:
                with open(file_path, 'w') as f:
                    f.write(modified)
    
    def run(self):
        """Run the migration"""
        print(f"Running migration (dry_run={self.dry_run})")
        
        # Find all Python files
        for py_file in Path('.').glob('**/*.py'):
            if any(skip in str(py_file) for skip in ['worktree', 'organized', '__pycache__']):
                continue
            self.migrate_python_imports(py_file)
            self.migrate_paths(py_file)
            
        # Find all shell scripts
        for sh_file in Path('.').glob('**/*.sh'):
            if any(skip in str(sh_file) for skip in ['worktree', 'organized']):
                continue
            self.migrate_paths(sh_file)
            
        print(f"\nTotal changes: {len(self.changes)}")
        for change in self.changes:
            print(f"  - {change}")
            
if __name__ == "__main__":
    dry_run = '--dry-run' in sys.argv
    migrator = RootMigrator(dry_run=dry_run)
    migrator.run()
```

## Risk Assessment

### Low Risk Items:
- Python import updates (mechanical, easy to test)
- Creating backup (no system changes)
- Running tests (read-only operations)

### Medium Risk Items:
- Shell script path updates (could break automation)
- Moving ngrok.yml (could affect webhook URL)
- Absolute path updates (might miss some)

### High Risk Items:
- None identified - this is a structural change, not a logic change

## Recommendation

**This migration is SAFE and MANAGEABLE** with proper precautions:

1. **Use version control**: Work in a branch, test thoroughly
2. **Automate changes**: Use the migration script to avoid manual errors
3. **Test incrementally**: Verify each component works after changes
4. **Keep backups**: Both file backups and git history
5. **Time it right**: Do this when markets are closed

The biggest "difficulty" is just being thorough - the changes themselves are straightforward.
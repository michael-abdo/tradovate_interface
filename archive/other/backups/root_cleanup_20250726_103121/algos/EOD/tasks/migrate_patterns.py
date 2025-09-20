#!/usr/bin/env python3
"""
Pattern Migration Script - Automated replacement of common code patterns.

This script identifies and replaces common duplicated patterns with canonical implementations:
1. Exception handling patterns
2. Timestamp generation
3. JSON serialization
4. Logger initialization
5. Path construction
"""

import os
import re
import ast
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass

@dataclass
class PatternMatch:
    file_path: str
    line_number: int
    original_code: str
    replacement_code: str
    pattern_type: str
    confidence: float = 1.0

class PatternMigrator:
    def __init__(self, root_dir: str = "./tasks"):
        self.root_dir = Path(root_dir)
        self.matches: List[PatternMatch] = []
        
    def find_exception_patterns(self) -> List[PatternMatch]:
        """Find exception handling patterns to replace."""
        patterns = []
        
        # Pattern 1: Basic except Exception as e
        exception_pattern = re.compile(
            r'except\s+Exception\s+as\s+(\w+):\s*\n(\s+)(.*?)(?=\n\s*(?:except|finally|else|\S|\Z))',
            re.MULTILINE | re.DOTALL
        )
        
        # Pattern 2: try/except with logging
        try_except_logging = re.compile(
            r'try:\s*\n(.*?)\nexcept\s+Exception\s+as\s+(\w+):\s*\n(\s+).*?\.error\(.*?\)\s*\n(?:\3.*?\n)*',
            re.MULTILINE | re.DOTALL
        )
        
        for py_file in self.root_dir.rglob("*.py"):
            if any(skip in str(py_file) for skip in ['__pycache__', 'test_', 'migration']):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Find basic exception patterns
                for match in exception_pattern.finditer(content):
                    line_num = content[:match.start()].count('\n') + 1
                    
                    # Skip if it's already using our decorator
                    if '@safe_execute' in content[max(0, match.start()-200):match.start()]:
                        continue
                    
                    original = match.group(0)
                    
                    # Generate replacement using safe_execute decorator
                    replacement = self._generate_exception_replacement(original, match)
                    
                    patterns.append(PatternMatch(
                        file_path=str(py_file),
                        line_number=line_num,
                        original_code=original.strip(),
                        replacement_code=replacement,
                        pattern_type="exception_handling",
                        confidence=0.8
                    ))
                    
            except Exception as e:
                print(f"Error processing {py_file}: {e}")
        
        return patterns
    
    def find_timestamp_patterns(self) -> List[PatternMatch]:
        """Find timestamp generation patterns to replace."""
        patterns = []
        
        # Pattern: get_utc_timestamp()
        timestamp_pattern = re.compile(r'datetime\.now\(\)\.isoformat\(\)')
        
        # Pattern: get_utc_timestamp()
        utc_timestamp_pattern = re.compile(r'datetime\.now\(timezone\.utc\)\.isoformat\(\)')
        
        for py_file in self.root_dir.rglob("*.py"):
            if any(skip in str(py_file) for skip in ['__pycache__', 'test_', 'migration']):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
                    # Check for UTC timestamp pattern
                    if utc_timestamp_pattern.search(line):
                        patterns.append(PatternMatch(
                            file_path=str(py_file),
                            line_number=i + 1,
                            original_code=line.strip(),
                            replacement_code=line.replace('get_utc_timestamp()', 'get_utc_timestamp()'),
                            pattern_type="timestamp_generation"
                        ))
                    
                    # Check for basic timestamp pattern
                    elif timestamp_pattern.search(line) and 'timezone.utc' not in line:
                        patterns.append(PatternMatch(
                            file_path=str(py_file),
                            line_number=i + 1,
                            original_code=line.strip(),
                            replacement_code=line.replace('get_utc_timestamp()', 'get_utc_timestamp()'),
                            pattern_type="timestamp_generation"
                        ))
                        
            except Exception as e:
                print(f"Error processing {py_file}: {e}")
        
        return patterns
    
    def find_json_patterns(self) -> List[PatternMatch]:
        """Find JSON serialization patterns to replace."""
        patterns = []
        
        # Pattern: json.dump with indent=2
        json_dump_pattern = re.compile(r'json\.dump\((.*?),\s*(.*?),\s*indent=2\)')
        
        # Pattern: json.dumps with indent=2
        json_dumps_pattern = re.compile(r'json\.dumps\((.*?),\s*indent=2\)')
        
        for py_file in self.root_dir.rglob("*.py"):
            if any(skip in str(py_file) for skip in ['__pycache__', 'test_', 'migration']):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
                    # Check for json.dump patterns
                    dump_match = json_dump_pattern.search(line)
                    if dump_match:
                        data_arg = dump_match.group(1)
                        file_arg = dump_match.group(2)
                        
                        replacement = f"save_json({data_arg}, {file_arg}).result"
                        
                        patterns.append(PatternMatch(
                            file_path=str(py_file),
                            line_number=i + 1,
                            original_code=line.strip(),
                            replacement_code=line.replace(dump_match.group(0), replacement),
                            pattern_type="json_serialization"
                        ))
                    
                    # Check for json.dumps patterns  
                    dumps_match = json_dumps_pattern.search(line)
                    if dumps_match:
                        data_arg = dumps_match.group(1)
                        replacement = f"to_json_string({data_arg}, indent=2)"
                        
                        patterns.append(PatternMatch(
                            file_path=str(py_file),
                            line_number=i + 1,
                            original_code=line.strip(),
                            replacement_code=line.replace(dumps_match.group(0), replacement),
                            pattern_type="json_serialization"
                        ))
                        
            except Exception as e:
                print(f"Error processing {py_file}: {e}")
        
        return patterns
    
    def find_logger_patterns(self) -> List[PatternMatch]:
        """Find logger initialization patterns to replace."""
        patterns = []
        
        # Pattern: get_logger()
        logger_pattern = re.compile(r'logging\.getLogger\(__name__\)')
        
        # Pattern: get_logger("name")
        logger_named_pattern = re.compile(r'logging\.getLogger\(["\']([^"\']+)["\']\)')
        
        for py_file in self.root_dir.rglob("*.py"):
            if any(skip in str(py_file) for skip in ['__pycache__', 'test_', 'migration']):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
                    # Check for logger patterns
                    if logger_pattern.search(line):
                        patterns.append(PatternMatch(
                            file_path=str(py_file),
                            line_number=i + 1,
                            original_code=line.strip(),
                            replacement_code=line.replace('get_logger()', 'get_logger()'),
                            pattern_type="logger_initialization"
                        ))
                    
                    named_match = logger_named_pattern.search(line)
                    if named_match:
                        logger_name = named_match.group(1)
                        replacement = f'get_logger("{logger_name}")'
                        
                        patterns.append(PatternMatch(
                            file_path=str(py_file),
                            line_number=i + 1,
                            original_code=line.strip(),
                            replacement_code=line.replace(named_match.group(0), replacement),
                            pattern_type="logger_initialization"
                        ))
                        
            except Exception as e:
                print(f"Error processing {py_file}: {e}")
        
        return patterns
    
    def find_path_patterns(self) -> List[PatternMatch]:
        """Find path construction patterns to replace."""
        patterns = []
        
        # Pattern: PathManager.get_project_root()
        path_pattern = re.compile(
            r'os\.path\.dirname\(os\.path\.abspath\(__file__\)\)'
        )
        
        # Pattern: complex nested dirname calls
        nested_dirname = re.compile(
            r'os\.path\.dirname\(os\.path\.dirname\(.*?__file__.*?\)\)'
        )
        
        for py_file in self.root_dir.rglob("*.py"):
            if any(skip in str(py_file) for skip in ['__pycache__', 'test_', 'migration']):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
                    # Check for path patterns
                    if path_pattern.search(line):
                        patterns.append(PatternMatch(
                            file_path=str(py_file),
                            line_number=i + 1,
                            original_code=line.strip(),
                            replacement_code=line.replace(
                                'PathManager.get_project_root()',
                                'PathManager.get_project_root()'
                            ),
                            pattern_type="path_construction"
                        ))
                    
                    # Check for nested dirname patterns
                    elif nested_dirname.search(line):
                        # This is more complex - might need project root
                        patterns.append(PatternMatch(
                            file_path=str(py_file),
                            line_number=i + 1,
                            original_code=line.strip(),
                            replacement_code=f"# TODO: Replace with PathManager.get_project_root() - {line.strip()}",
                            pattern_type="path_construction",
                            confidence=0.5
                        ))
                        
            except Exception as e:
                print(f"Error processing {py_file}: {e}")
        
        return patterns
    
    def _generate_exception_replacement(self, original: str, match: re.Match) -> str:
        """Generate replacement code for exception handling."""
        # This is a simplified replacement - would need more sophisticated analysis
        return "@safe_execute(operation='TODO: add operation description')\ndef safe_operation():\n    # TODO: Move try block content here\n    pass"
    
    def find_all_patterns(self) -> Dict[str, List[PatternMatch]]:
        """Find all patterns across the codebase."""
        all_patterns = {}
        
        print("🔍 Scanning for exception handling patterns...")
        all_patterns['exception_handling'] = self.find_exception_patterns()
        
        print("🔍 Scanning for timestamp patterns...")
        all_patterns['timestamp_generation'] = self.find_timestamp_patterns()
        
        print("🔍 Scanning for JSON patterns...")
        all_patterns['json_serialization'] = self.find_json_patterns()
        
        print("🔍 Scanning for logger patterns...")
        all_patterns['logger_initialization'] = self.find_logger_patterns()
        
        print("🔍 Scanning for path patterns...")
        all_patterns['path_construction'] = self.find_path_patterns()
        
        return all_patterns
    
    def apply_replacements(self, patterns: List[PatternMatch], dry_run: bool = True) -> int:
        """Apply pattern replacements to files."""
        files_modified = 0
        
        # Group patterns by file
        by_file = {}
        for pattern in patterns:
            if pattern.file_path not in by_file:
                by_file[pattern.file_path] = []
            by_file[pattern.file_path].append(pattern)
        
        for file_path, file_patterns in by_file.items():
            if dry_run:
                print(f"\n📝 Would modify {file_path}:")
                for pattern in file_patterns:
                    print(f"  Line {pattern.line_number}: {pattern.pattern_type}")
                    print(f"    - {pattern.original_code}")
                    print(f"    + {pattern.replacement_code}")
            else:
                # Actually apply changes
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    lines = content.split('\n')
                    
                    # Sort patterns by line number in reverse order to avoid offset issues
                    file_patterns.sort(key=lambda p: p.line_number, reverse=True)
                    
                    for pattern in file_patterns:
                        if pattern.line_number <= len(lines):
                            lines[pattern.line_number - 1] = pattern.replacement_code
                    
                    # Write back to file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(lines))
                    
                    files_modified += 1
                    print(f"✅ Modified {file_path}")
                    
                except Exception as e:
                    print(f"❌ Error modifying {file_path}: {e}")
        
        return files_modified

def main():
    parser = argparse.ArgumentParser(description="Migrate common code patterns")
    parser.add_argument("--pattern", choices=['exception', 'timestamp', 'json', 'logger', 'path', 'all'],
                       default='all', help="Pattern type to migrate")
    parser.add_argument("--dry-run", action='store_true', help="Show changes without applying them")
    parser.add_argument("--apply", action='store_true', help="Actually apply the changes")
    parser.add_argument("--root", default="./tasks", help="Root directory to scan")
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.apply:
        print("⚠️  Must specify either --dry-run or --apply")
        return
    
    migrator = PatternMigrator(args.root)
    
    print("🚀 Starting pattern migration analysis...")
    print("=" * 60)
    
    all_patterns = migrator.find_all_patterns()
    
    # Show summary
    print("\n📊 PATTERN ANALYSIS SUMMARY:")
    print("-" * 40)
    total_patterns = 0
    for pattern_type, patterns in all_patterns.items():
        count = len(patterns)
        total_patterns += count
        print(f"{pattern_type}: {count} instances")
    
    print(f"\nTotal patterns found: {total_patterns}")
    
    if args.pattern == 'all':
        patterns_to_process = []
        for pattern_list in all_patterns.values():
            patterns_to_process.extend(pattern_list)
    else:
        pattern_map = {
            'exception': 'exception_handling',
            'timestamp': 'timestamp_generation',
            'json': 'json_serialization',
            'logger': 'logger_initialization',
            'path': 'path_construction'
        }
        pattern_key = pattern_map.get(args.pattern, args.pattern)
        patterns_to_process = all_patterns.get(pattern_key, [])
    
    if patterns_to_process:
        print(f"\n🔧 Processing {len(patterns_to_process)} patterns...")
        
        files_modified = migrator.apply_replacements(patterns_to_process, dry_run=args.dry_run)
        
        if args.apply:
            print(f"\n✅ Migration complete! Modified {files_modified} files.")
        else:
            print(f"\n💡 Dry run complete. Would modify {len(set(p.file_path for p in patterns_to_process))} files.")
            print("Run with --apply to make actual changes.")
    else:
        print("🎉 No patterns found to migrate!")

if __name__ == "__main__":
    main()
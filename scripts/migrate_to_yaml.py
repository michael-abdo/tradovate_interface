#!/usr/bin/env python3
"""
Migration script to convert JSON configuration files to YAML format.
"""

import json
import yaml
import argparse
import sys
from pathlib import Path


def read_json_file(json_path: Path) -> dict:
    """Read and parse a JSON file."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {json_path}: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File not found: {json_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading {json_path}: {e}")
        sys.exit(1)


def write_yaml_file(yaml_path: Path, data: dict, preserve_order: bool = True) -> None:
    """Write data to a YAML file with nice formatting."""
    try:
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                data, 
                f, 
                default_flow_style=False,  # Use block style, not inline
                sort_keys=not preserve_order,  # Preserve original order by default
                allow_unicode=True,  # Allow unicode characters
                width=1000  # Prevent line wrapping
            )
        print(f"✅ Successfully created: {yaml_path}")
    except Exception as e:
        print(f"Error writing {yaml_path}: {e}")
        sys.exit(1)


def migrate_file(json_path: Path, yaml_path: Path = None, backup: bool = True) -> None:
    """Migrate a single JSON file to YAML format."""
    # Determine output path
    if yaml_path is None:
        yaml_path = json_path.with_suffix('.yaml')
    
    # Check if YAML already exists
    if yaml_path.exists():
        response = input(f"⚠️  {yaml_path} already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Skipping...")
            return
    
    # Read JSON data
    print(f"📖 Reading: {json_path}")
    data = read_json_file(json_path)
    
    # Write YAML data
    print(f"📝 Writing: {yaml_path}")
    write_yaml_file(yaml_path, data)
    
    # Create backup if requested
    if backup and not json_path.name.endswith('.bak'):
        backup_path = json_path.with_suffix('.json.bak')
        print(f"💾 Creating backup: {backup_path}")
        json_path.rename(backup_path)
        print(f"   Original JSON moved to backup")


def main():
    parser = argparse.ArgumentParser(
        description="Convert JSON configuration files to YAML format"
    )
    parser.add_argument(
        "files", 
        nargs="+", 
        help="JSON file(s) to convert"
    )
    parser.add_argument(
        "--no-backup", 
        action="store_true", 
        help="Don't create backup of original JSON files"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output filename (only valid with single input file)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.output and len(args.files) > 1:
        print("Error: --output can only be used with a single input file")
        sys.exit(1)
    
    # Process each file
    for file_path in args.files:
        json_path = Path(file_path)
        
        # Determine output path
        yaml_path = Path(args.output) if args.output else None
        
        # Perform migration
        migrate_file(json_path, yaml_path, backup=not args.no_backup)
    
    print("\n✨ Migration complete!")


if __name__ == "__main__":
    main()
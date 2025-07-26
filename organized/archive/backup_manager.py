#!/usr/bin/env python3
"""
Backup Manager - Creates timestamped backups with rollback capability
"""

import os
import shutil
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class BackupManager:
    def __init__(self, backup_dir: str = "backups/chrome_restart"):
        self.backup_dir = Path(backup_dir)
        self.backup_manifest_file = self.backup_dir / "backup_manifest.json"
        self.files_to_backup = [
            "/Users/Mike/trading/start_all.py",
            "/Users/Mike/trading/src/auto_login.py",
            "/Users/Mike/trading/tradovate_interface/src/utils/process_monitor.py",
            "/Users/Mike/trading/config/connection_health.json",
            "/Users/Mike/trading/tradovate_interface/config/process_monitor.json"
        ]
        self._ensure_backup_dir()
    
    def _ensure_backup_dir(self):
        """Create backup directory if it doesn't exist"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _calculate_checksum(self, filepath: str) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _load_manifest(self) -> Dict:
        """Load backup manifest"""
        if self.backup_manifest_file.exists():
            with open(self.backup_manifest_file, 'r') as f:
                return json.load(f)
        return {"backups": []}
    
    def _save_manifest(self, manifest: Dict):
        """Save backup manifest"""
        with open(self.backup_manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
    
    def create_backup(self, description: str = "Manual backup") -> str:
        """Create a timestamped backup of all files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"backup_{timestamp}"
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(exist_ok=True)
        
        backup_info = {
            "id": backup_id,
            "timestamp": timestamp,
            "description": description,
            "files": []
        }
        
        print(f"\n🔒 Creating backup: {backup_id}")
        print(f"   Description: {description}")
        
        for file_path in self.files_to_backup:
            if os.path.exists(file_path):
                # Calculate original file checksum
                original_checksum = self._calculate_checksum(file_path)
                
                # Create backup subdirectory structure
                relative_path = os.path.relpath(file_path, '/')
                backup_file_path = backup_path / relative_path
                backup_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(file_path, backup_file_path)
                
                # Verify backup
                backup_checksum = self._calculate_checksum(backup_file_path)
                
                if original_checksum == backup_checksum:
                    print(f"   ✓ Backed up: {file_path}")
                    backup_info["files"].append({
                        "original_path": file_path,
                        "backup_path": str(backup_file_path),
                        "checksum": original_checksum,
                        "size": os.path.getsize(file_path)
                    })
                else:
                    print(f"   ✗ Backup verification failed: {file_path}")
                    raise Exception(f"Backup verification failed for {file_path}")
            else:
                print(f"   ⚠ File not found: {file_path}")
        
        # Update manifest
        manifest = self._load_manifest()
        manifest["backups"].append(backup_info)
        self._save_manifest(manifest)
        
        print(f"\n✅ Backup created successfully: {backup_id}")
        return backup_id
    
    def list_backups(self) -> List[Dict]:
        """List all available backups"""
        manifest = self._load_manifest()
        return manifest.get("backups", [])
    
    def verify_backup(self, backup_id: str) -> bool:
        """Verify integrity of a backup"""
        manifest = self._load_manifest()
        backup_info = None
        
        for backup in manifest["backups"]:
            if backup["id"] == backup_id:
                backup_info = backup
                break
        
        if not backup_info:
            print(f"❌ Backup not found: {backup_id}")
            return False
        
        print(f"\n🔍 Verifying backup: {backup_id}")
        all_valid = True
        
        for file_info in backup_info["files"]:
            backup_path = file_info["backup_path"]
            expected_checksum = file_info["checksum"]
            
            if os.path.exists(backup_path):
                actual_checksum = self._calculate_checksum(backup_path)
                if actual_checksum == expected_checksum:
                    print(f"   ✓ Valid: {file_info['original_path']}")
                else:
                    print(f"   ✗ Corrupted: {file_info['original_path']}")
                    all_valid = False
            else:
                print(f"   ✗ Missing: {file_info['original_path']}")
                all_valid = False
        
        return all_valid
    
    def rollback(self, backup_id: str, dry_run: bool = False) -> bool:
        """Rollback to a previous backup"""
        manifest = self._load_manifest()
        backup_info = None
        
        for backup in manifest["backups"]:
            if backup["id"] == backup_id:
                backup_info = backup
                break
        
        if not backup_info:
            print(f"❌ Backup not found: {backup_id}")
            return False
        
        # Verify backup first
        if not self.verify_backup(backup_id):
            print(f"❌ Cannot rollback - backup verification failed")
            return False
        
        if dry_run:
            print(f"\n🔄 DRY RUN - Rollback to: {backup_id}")
        else:
            print(f"\n🔄 Rolling back to: {backup_id}")
        
        # Create a safety backup of current state
        if not dry_run:
            safety_backup_id = self.create_backup(f"Pre-rollback safety backup (before {backup_id})")
        
        # Perform rollback
        for file_info in backup_info["files"]:
            original_path = file_info["original_path"]
            backup_path = file_info["backup_path"]
            
            if dry_run:
                print(f"   Would restore: {original_path}")
            else:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(original_path), exist_ok=True)
                
                # Copy backup file to original location
                shutil.copy2(backup_path, original_path)
                
                # Verify restoration
                restored_checksum = self._calculate_checksum(original_path)
                if restored_checksum == file_info["checksum"]:
                    print(f"   ✓ Restored: {original_path}")
                else:
                    print(f"   ✗ Restoration failed: {original_path}")
                    return False
        
        if not dry_run:
            print(f"\n✅ Rollback completed successfully")
            print(f"   Safety backup created: {safety_backup_id}")
        else:
            print(f"\n✅ Dry run completed - no changes made")
        
        return True
    
    def cleanup_old_backups(self, keep_count: int = 5):
        """Remove old backups, keeping the most recent ones"""
        manifest = self._load_manifest()
        backups = manifest.get("backups", [])
        
        if len(backups) <= keep_count:
            print(f"No cleanup needed - only {len(backups)} backups exist")
            return
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Identify backups to remove
        to_remove = backups[keep_count:]
        
        print(f"\n🧹 Cleaning up old backups (keeping {keep_count} most recent)")
        
        for backup in to_remove:
            backup_path = self.backup_dir / backup["id"]
            if backup_path.exists():
                shutil.rmtree(backup_path)
                print(f"   ✓ Removed: {backup['id']}")
        
        # Update manifest
        manifest["backups"] = backups[:keep_count]
        self._save_manifest(manifest)
        
        print(f"✅ Cleanup completed - removed {len(to_remove)} old backups")


def main():
    """CLI for backup management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Backup Manager for Chrome Restart Implementation")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Create backup command
    create_parser = subparsers.add_parser('create', help='Create a new backup')
    create_parser.add_argument('-d', '--description', default='Manual backup', help='Backup description')
    
    # List backups command
    list_parser = subparsers.add_parser('list', help='List all backups')
    
    # Verify backup command
    verify_parser = subparsers.add_parser('verify', help='Verify backup integrity')
    verify_parser.add_argument('backup_id', help='Backup ID to verify')
    
    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback to a backup')
    rollback_parser.add_argument('backup_id', help='Backup ID to rollback to')
    rollback_parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Remove old backups')
    cleanup_parser.add_argument('-k', '--keep', type=int, default=5, help='Number of recent backups to keep')
    
    args = parser.parse_args()
    
    manager = BackupManager()
    
    if args.command == 'create':
        manager.create_backup(args.description)
    
    elif args.command == 'list':
        backups = manager.list_backups()
        if backups:
            print("\n📦 Available backups:")
            for backup in backups:
                print(f"\n   ID: {backup['id']}")
                print(f"   Date: {backup['timestamp']}")
                print(f"   Description: {backup['description']}")
                print(f"   Files: {len(backup['files'])}")
        else:
            print("No backups found")
    
    elif args.command == 'verify':
        manager.verify_backup(args.backup_id)
    
    elif args.command == 'rollback':
        manager.rollback(args.backup_id, dry_run=args.dry_run)
    
    elif args.command == 'cleanup':
        manager.cleanup_old_backups(args.keep)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
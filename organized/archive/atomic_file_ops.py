#!/usr/bin/env python3
"""
Atomic File Operations - Safe file modifications with verification
"""

import os
import shutil
import tempfile
import hashlib
import json
from pathlib import Path
from typing import Optional, Callable, Any
from contextlib import contextmanager
import fcntl
import time

from structured_logger import get_logger


class AtomicFileOperationError(Exception):
    """Custom exception for atomic file operation failures"""
    pass


class AtomicFileOps:
    """Provides atomic file operations with verification and rollback"""
    
    def __init__(self):
        self.logger = get_logger("atomic_file_ops", log_file="operations/file_ops.log")
        self.operation_id = 0
    
    def _generate_operation_id(self) -> str:
        """Generate unique operation ID"""
        self.operation_id += 1
        timestamp = int(time.time() * 1000)
        return f"op_{timestamp}_{self.operation_id}"
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _verify_file_integrity(self, file_path: str, expected_checksum: Optional[str] = None) -> bool:
        """Verify file integrity"""
        if not os.path.exists(file_path):
            return False
        
        if expected_checksum:
            actual_checksum = self._calculate_checksum(file_path)
            return actual_checksum == expected_checksum
        
        # Basic integrity checks if no checksum provided
        try:
            stat = os.stat(file_path)
            return stat.st_size > 0  # File should not be empty
        except Exception:
            return False
    
    @contextmanager
    def file_lock(self, file_path: str, timeout: int = 10):
        """Context manager for file locking"""
        lock_file = f"{file_path}.lock"
        lock_fd = None
        op_id = self._generate_operation_id()
        
        try:
            # Create lock file
            lock_fd = open(lock_file, 'w')
            
            # Try to acquire exclusive lock
            start_time = time.time()
            while True:
                try:
                    fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except IOError:
                    if time.time() - start_time > timeout:
                        raise AtomicFileOperationError(f"Failed to acquire lock for {file_path} after {timeout}s")
                    time.sleep(0.1)
            
            self.logger.info("File lock acquired", operation_id=op_id, file_path=file_path)
            yield
            
        finally:
            # Release lock
            if lock_fd:
                try:
                    fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
                    lock_fd.close()
                    os.unlink(lock_file)
                    self.logger.info("File lock released", operation_id=op_id, file_path=file_path)
                except Exception as e:
                    self.logger.error("Error releasing lock", operation_id=op_id, error=str(e))
    
    def atomic_write(self, 
                    file_path: str, 
                    content: str, 
                    mode: str = 'w',
                    backup: bool = True,
                    verify: bool = True) -> bool:
        """Atomically write content to a file"""
        op_id = self._generate_operation_id()
        file_path = os.path.abspath(file_path)
        backup_path = None
        temp_path = None
        
        self.logger.info("Starting atomic write", 
                        operation_id=op_id,
                        file_path=file_path,
                        content_size=len(content),
                        mode=mode)
        
        try:
            with self.file_lock(file_path):
                # Create backup if requested and file exists
                if backup and os.path.exists(file_path):
                    backup_path = f"{file_path}.backup.{op_id}"
                    shutil.copy2(file_path, backup_path)
                    backup_checksum = self._calculate_checksum(backup_path)
                    self.logger.info("Created backup", 
                                   operation_id=op_id,
                                   backup_path=backup_path,
                                   checksum=backup_checksum)
                
                # Write to temporary file
                temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(file_path))
                try:
                    with os.fdopen(temp_fd, mode) as temp_file:
                        temp_file.write(content)
                        temp_file.flush()
                        os.fsync(temp_file.fileno())
                except Exception:
                    os.close(temp_fd)
                    raise
                
                # Verify temporary file if requested
                if verify:
                    temp_checksum = self._calculate_checksum(temp_path)
                    if not self._verify_file_integrity(temp_path):
                        raise AtomicFileOperationError("Temporary file verification failed")
                    self.logger.info("Temporary file verified", 
                                   operation_id=op_id,
                                   checksum=temp_checksum)
                
                # Copy file permissions
                if os.path.exists(file_path):
                    shutil.copystat(file_path, temp_path)
                
                # Atomic rename
                os.rename(temp_path, file_path)
                
                self.logger.info("Atomic write completed", 
                               operation_id=op_id,
                               file_path=file_path)
                
                # Clean up backup on success
                if backup_path and os.path.exists(backup_path):
                    os.unlink(backup_path)
                
                return True
                
        except Exception as e:
            self.logger.error("Atomic write failed", 
                            operation_id=op_id,
                            file_path=file_path,
                            error=str(e))
            
            # Restore from backup if available
            if backup_path and os.path.exists(backup_path):
                try:
                    shutil.copy2(backup_path, file_path)
                    self.logger.info("Restored from backup", 
                                   operation_id=op_id,
                                   backup_path=backup_path)
                except Exception as restore_error:
                    self.logger.error("Backup restoration failed", 
                                    operation_id=op_id,
                                    error=str(restore_error))
            
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
            
            raise AtomicFileOperationError(f"Atomic write failed: {e}")
    
    def atomic_update(self,
                     file_path: str,
                     update_func: Callable[[str], str],
                     backup: bool = True,
                     verify: bool = True) -> bool:
        """Atomically update a file using a transformation function"""
        op_id = self._generate_operation_id()
        
        self.logger.info("Starting atomic update", 
                        operation_id=op_id,
                        file_path=file_path)
        
        try:
            # Read current content
            with open(file_path, 'r') as f:
                original_content = f.read()
            
            # Apply transformation
            updated_content = update_func(original_content)
            
            # Use atomic_write to save
            return self.atomic_write(file_path, updated_content, backup=backup, verify=verify)
            
        except Exception as e:
            self.logger.error("Atomic update failed", 
                            operation_id=op_id,
                            file_path=file_path,
                            error=str(e))
            raise AtomicFileOperationError(f"Atomic update failed: {e}")
    
    def atomic_json_update(self,
                          file_path: str,
                          update_func: Callable[[dict], dict],
                          backup: bool = True,
                          verify: bool = True,
                          indent: int = 2) -> bool:
        """Atomically update a JSON file"""
        op_id = self._generate_operation_id()
        
        self.logger.info("Starting atomic JSON update", 
                        operation_id=op_id,
                        file_path=file_path)
        
        def json_transformer(content: str) -> str:
            """Transform JSON content"""
            data = json.loads(content)
            updated_data = update_func(data)
            return json.dumps(updated_data, indent=indent)
        
        try:
            return self.atomic_update(file_path, json_transformer, backup=backup, verify=verify)
        except json.JSONDecodeError as e:
            self.logger.error("JSON parsing error", 
                            operation_id=op_id,
                            error=str(e))
            raise AtomicFileOperationError(f"JSON parsing error: {e}")
    
    def safe_append(self,
                   file_path: str,
                   content: str,
                   max_size: Optional[int] = None) -> bool:
        """Safely append content to a file with optional size limit"""
        op_id = self._generate_operation_id()
        
        self.logger.info("Starting safe append", 
                        operation_id=op_id,
                        file_path=file_path,
                        content_size=len(content))
        
        try:
            with self.file_lock(file_path):
                # Check current file size
                if max_size and os.path.exists(file_path):
                    current_size = os.path.getsize(file_path)
                    if current_size + len(content) > max_size:
                        self.logger.warning("File size limit would be exceeded", 
                                          operation_id=op_id,
                                          current_size=current_size,
                                          max_size=max_size)
                        return False
                
                # Append content
                with open(file_path, 'a') as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())
                
                self.logger.info("Safe append completed", operation_id=op_id)
                return True
                
        except Exception as e:
            self.logger.error("Safe append failed", 
                            operation_id=op_id,
                            error=str(e))
            raise AtomicFileOperationError(f"Safe append failed: {e}")
    
    def atomic_copy(self,
                   source_path: str,
                   dest_path: str,
                   backup_dest: bool = True,
                   verify: bool = True) -> bool:
        """Atomically copy a file"""
        op_id = self._generate_operation_id()
        
        self.logger.info("Starting atomic copy", 
                        operation_id=op_id,
                        source=source_path,
                        destination=dest_path)
        
        try:
            # Read source content
            with open(source_path, 'rb') as f:
                content = f.read()
            
            # Calculate source checksum for verification
            source_checksum = self._calculate_checksum(source_path) if verify else None
            
            # Write to destination atomically
            with self.file_lock(dest_path):
                backup_path = None
                
                # Backup destination if it exists
                if backup_dest and os.path.exists(dest_path):
                    backup_path = f"{dest_path}.backup.{op_id}"
                    shutil.copy2(dest_path, backup_path)
                
                # Write content
                temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(dest_path))
                try:
                    with os.fdopen(temp_fd, 'wb') as temp_file:
                        temp_file.write(content)
                        temp_file.flush()
                        os.fsync(temp_file.fileno())
                except Exception:
                    os.close(temp_fd)
                    raise
                
                # Verify if requested
                if verify:
                    dest_checksum = self._calculate_checksum(temp_path)
                    if dest_checksum != source_checksum:
                        raise AtomicFileOperationError("Copy verification failed - checksums don't match")
                
                # Copy permissions
                shutil.copystat(source_path, temp_path)
                
                # Atomic rename
                os.rename(temp_path, dest_path)
                
                # Clean up backup
                if backup_path and os.path.exists(backup_path):
                    os.unlink(backup_path)
                
                self.logger.info("Atomic copy completed", 
                               operation_id=op_id,
                               checksum=source_checksum if verify else "not_verified")
                return True
                
        except Exception as e:
            self.logger.error("Atomic copy failed", 
                            operation_id=op_id,
                            error=str(e))
            raise AtomicFileOperationError(f"Atomic copy failed: {e}")


def test_atomic_operations():
    """Test atomic file operations"""
    print("🧪 Testing Atomic File Operations\n")
    
    ops = AtomicFileOps()
    test_file = "test_atomic.txt"
    test_json = "test_atomic.json"
    
    try:
        # Test 1: Atomic write
        print("1. Testing atomic write...")
        ops.atomic_write(test_file, "Hello, World!\n")
        print("   ✅ Write successful")
        
        # Test 2: Atomic update
        print("\n2. Testing atomic update...")
        def update_func(content: str) -> str:
            return content + "Updated content\n"
        
        ops.atomic_update(test_file, update_func)
        print("   ✅ Update successful")
        
        # Test 3: Atomic JSON update
        print("\n3. Testing atomic JSON update...")
        # Create initial JSON
        initial_data = {"version": 1, "status": "active"}
        with open(test_json, 'w') as f:
            json.dump(initial_data, f)
        
        def json_update_func(data: dict) -> dict:
            data["version"] += 1
            data["updated_at"] = time.time()
            return data
        
        ops.atomic_json_update(test_json, json_update_func)
        print("   ✅ JSON update successful")
        
        # Test 4: Safe append
        print("\n4. Testing safe append...")
        ops.safe_append(test_file, "Appended line\n", max_size=1024)
        print("   ✅ Append successful")
        
        # Test 5: Atomic copy
        print("\n5. Testing atomic copy...")
        copy_file = "test_atomic_copy.txt"
        ops.atomic_copy(test_file, copy_file)
        print("   ✅ Copy successful")
        
        # Clean up
        for f in [test_file, test_json, copy_file]:
            if os.path.exists(f):
                os.unlink(f)
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        # Clean up
        for f in [test_file, test_json, "test_atomic_copy.txt"]:
            if os.path.exists(f):
                os.unlink(f)


if __name__ == "__main__":
    test_atomic_operations()
#!/usr/bin/env python3
"""
Chrome Path Finder - Cross-platform Chrome executable discovery
Uses dependency injection pattern for flexibility
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional, Callable
from abc import ABC, abstractmethod


class ChromePathStrategy(ABC):
    """Abstract base class for Chrome path finding strategies"""
    
    @abstractmethod
    def find_chrome_paths(self) -> List[str]:
        """Return list of potential Chrome executable paths"""
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Return platform name"""
        pass


class MacOSChromeStrategy(ChromePathStrategy):
    """Chrome path strategy for macOS"""
    
    def find_chrome_paths(self) -> List[str]:
        return [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Chromium.app/Contents/MacOS/Chromium',
            '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary',
            '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',
            os.path.expanduser('~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
            '/usr/local/bin/google-chrome',
            '/usr/local/bin/chromium'
        ]
    
    def get_platform_name(self) -> str:
        return "macOS"


class LinuxChromeStrategy(ChromePathStrategy):
    """Chrome path strategy for Linux"""
    
    def find_chrome_paths(self) -> List[str]:
        return [
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            '/usr/bin/google-chrome-beta',
            '/usr/bin/google-chrome-unstable',
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
            '/snap/bin/chromium',
            '/usr/local/bin/google-chrome',
            '/usr/local/bin/chromium',
            os.path.expanduser('~/.local/bin/google-chrome'),
            os.path.expanduser('~/.local/bin/chromium')
        ]
    
    def get_platform_name(self) -> str:
        return "Linux"


class WindowsChromeStrategy(ChromePathStrategy):
    """Chrome path strategy for Windows"""
    
    def find_chrome_paths(self) -> List[str]:
        paths = []
        
        # Common Chrome locations on Windows
        program_files = [
            os.environ.get('PROGRAMFILES', 'C:\\Program Files'),
            os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'),
            os.environ.get('LOCALAPPDATA', '')
        ]
        
        chrome_paths = [
            'Google\\Chrome\\Application\\chrome.exe',
            'Chromium\\Application\\chromium.exe',
            'BraveSoftware\\Brave-Browser\\Application\\brave.exe'
        ]
        
        for base in program_files:
            if base:
                for chrome_path in chrome_paths:
                    paths.append(os.path.join(base, chrome_path))
        
        return paths
    
    def get_platform_name(self) -> str:
        return "Windows"


class ChromePathFinder:
    """Main Chrome path finder with dependency injection"""
    
    def __init__(self, strategy: Optional[ChromePathStrategy] = None):
        """Initialize with optional custom strategy"""
        if strategy:
            self.strategy = strategy
        else:
            # Auto-detect platform
            self.strategy = self._detect_platform_strategy()
        
        self._cached_chrome_path = None
        self._custom_paths = []
    
    def _detect_platform_strategy(self) -> ChromePathStrategy:
        """Detect platform and return appropriate strategy"""
        platform = sys.platform.lower()
        
        if platform == 'darwin':
            return MacOSChromeStrategy()
        elif platform.startswith('linux'):
            return LinuxChromeStrategy()
        elif platform.startswith('win'):
            return WindowsChromeStrategy()
        else:
            raise RuntimeError(f"Unsupported platform: {platform}")
    
    def add_custom_path(self, path: str):
        """Add a custom Chrome path to check"""
        self._custom_paths.append(path)
    
    def find_chrome(self, validate: bool = True) -> Optional[str]:
        """Find Chrome executable path"""
        # Return cached path if available
        if self._cached_chrome_path and os.path.exists(self._cached_chrome_path):
            return self._cached_chrome_path
        
        # Get all potential paths
        all_paths = self._custom_paths + self.strategy.find_chrome_paths()
        
        # Check each path
        for path in all_paths:
            if os.path.exists(path):
                if validate:
                    if self._validate_chrome_executable(path):
                        self._cached_chrome_path = path
                        return path
                else:
                    self._cached_chrome_path = path
                    return path
        
        # Try to find Chrome in PATH
        chrome_in_path = self._find_chrome_in_path()
        if chrome_in_path:
            self._cached_chrome_path = chrome_in_path
            return chrome_in_path
        
        return None
    
    def _validate_chrome_executable(self, path: str) -> bool:
        """Validate that the path is a working Chrome executable"""
        try:
            # Try to get Chrome version
            result = subprocess.run(
                [path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                # Check if output contains Chrome/Chromium
                if any(browser in output for browser in ['Chrome', 'Chromium', 'Brave']):
                    return True
        except Exception:
            pass
        
        return False
    
    def _find_chrome_in_path(self) -> Optional[str]:
        """Try to find Chrome in system PATH"""
        chrome_names = [
            'google-chrome',
            'google-chrome-stable',
            'chromium',
            'chromium-browser',
            'chrome',
            'brave',
            'brave-browser'
        ]
        
        for name in chrome_names:
            try:
                # Use 'which' on Unix-like systems, 'where' on Windows
                cmd = 'where' if sys.platform.startswith('win') else 'which'
                result = subprocess.run(
                    [cmd, name],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    path = result.stdout.strip()
                    if path and self._validate_chrome_executable(path):
                        return path
            except Exception:
                pass
        
        return None
    
    def get_chrome_info(self) -> dict:
        """Get information about the Chrome installation"""
        chrome_path = self.find_chrome()
        
        if not chrome_path:
            return {
                'found': False,
                'platform': self.strategy.get_platform_name(),
                'error': 'Chrome executable not found'
            }
        
        info = {
            'found': True,
            'path': chrome_path,
            'platform': self.strategy.get_platform_name()
        }
        
        # Get version
        try:
            result = subprocess.run(
                [chrome_path, '--version'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                info['version'] = result.stdout.strip()
        except Exception as e:
            info['version_error'] = str(e)
        
        # Get file info
        try:
            stat = os.stat(chrome_path)
            info['size'] = stat.st_size
            info['executable'] = os.access(chrome_path, os.X_OK)
        except Exception as e:
            info['stat_error'] = str(e)
        
        return info


# Factory function for easy use
def get_chrome_finder(custom_strategy: Optional[ChromePathStrategy] = None) -> ChromePathFinder:
    """Factory function to get ChromePathFinder instance"""
    return ChromePathFinder(custom_strategy)


# Convenience function for backward compatibility
def find_chrome_path() -> str:
    """Find Chrome path (raises exception if not found)"""
    finder = get_chrome_finder()
    path = finder.find_chrome()
    
    if not path:
        raise RuntimeError("Chrome executable not found. Please install Chrome or specify custom path.")
    
    return path


# Module-level instance for singleton pattern
_default_finder = None


def get_default_chrome_path() -> str:
    """Get Chrome path using default singleton finder"""
    global _default_finder
    if not _default_finder:
        _default_finder = get_chrome_finder()
    
    path = _default_finder.find_chrome()
    if not path:
        raise RuntimeError("Chrome executable not found")
    
    return path


def main():
    """CLI for Chrome path discovery"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Chrome Path Finder")
    parser.add_argument('--add-path', help="Add custom Chrome path to check")
    parser.add_argument('--no-validate', action='store_true', help="Skip Chrome executable validation")
    parser.add_argument('--json', action='store_true', help="Output in JSON format")
    
    args = parser.parse_args()
    
    finder = get_chrome_finder()
    
    if args.add_path:
        finder.add_custom_path(args.add_path)
    
    if args.json:
        import json
        info = finder.get_chrome_info()
        print(json.dumps(info, indent=2))
    else:
        info = finder.get_chrome_info()
        
        print("🔍 Chrome Path Finder\n")
        print(f"Platform: {info['platform']}")
        
        if info['found']:
            print(f"✅ Chrome found!")
            print(f"   Path: {info['path']}")
            if 'version' in info:
                print(f"   Version: {info['version']}")
            if 'size' in info:
                print(f"   Size: {info['size']:,} bytes")
            if 'executable' in info:
                print(f"   Executable: {'Yes' if info['executable'] else 'No'}")
        else:
            print(f"❌ Chrome not found")
            print(f"   Error: {info.get('error', 'Unknown error')}")
            print("\nTried the following locations:")
            for path in finder.strategy.find_chrome_paths():
                exists = "✓" if os.path.exists(path) else "✗"
                print(f"   {exists} {path}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
File Integrity Monitoring (FIM) for HIDS
Monitors critical system files and directories for unauthorized changes
"""

import hashlib
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set
import platform

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logging.warning("watchdog not installed. Install with: pip install watchdog")

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class FileIntegrityMonitor:
    """
    Monitors critical files and directories for unauthorized modifications
    """

    def __init__(self, config_file: str = None):
        """
        Initialize File Integrity Monitor

        Args:
            config_file: Path to configuration file
        """
        self.config = self._load_config(config_file)
        self.baseline = {}
        self.alerts = []
        self.stats = {
            'files_monitored': 0,
            'changes_detected': 0,
            'new_files': 0,
            'deleted_files': 0,
            'modified_files': 0
        }

    def _load_config(self, config_file: str) -> Dict:
        """Load monitoring configuration"""
        default_config = {
            'monitored_paths': self._get_default_paths(),
            'file_extensions': ['.exe', '.dll', '.sys', '.conf', '.ini', '.cfg'],
            'exclude_patterns': ['*.tmp', '*.log', '*.swp'],
            'check_interval': 60,  # seconds
            'hash_algorithm': 'sha256'
        }

        if config_file and Path(config_file).exists():
            with open(config_file, 'r') as f:
                import yaml
                user_config = yaml.safe_load(f)
                default_config.update(user_config)

        return default_config

    def _get_default_paths(self) -> List[str]:
        """Get default critical paths based on OS"""
        system = platform.system()

        if system == 'Windows':
            return [
                'C:\\Windows\\System32',
                'C:\\Windows\\SysWOW64',
                'C:\\Program Files',
                'C:\\Program Files (x86)',
                os.path.expandvars('%PROGRAMDATA%'),
                os.path.expandvars('%APPDATA%')
            ]
        elif system == 'Linux':
            return [
                '/etc',
                '/bin',
                '/sbin',
                '/usr/bin',
                '/usr/sbin',
                '/lib',
                '/boot'
            ]
        else:  # macOS
            return [
                '/etc',
                '/bin',
                '/sbin',
                '/usr/bin',
                '/usr/sbin',
                '/System',
                '/Library'
            ]

    def calculate_hash(self, filepath: str) -> str:
        """
        Calculate file hash

        Args:
            filepath: Path to file

        Returns:
            Hash string
        """
        algorithm = self.config.get('hash_algorithm', 'sha256')
        hasher = hashlib.new(algorithm)

        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Failed to hash {filepath}: {e}")
            return None

    def get_file_metadata(self, filepath: str) -> Dict:
        """
        Get file metadata

        Args:
            filepath: Path to file

        Returns:
            Metadata dictionary
        """
        try:
            stat = os.stat(filepath)
            return {
                'size': stat.st_size,
                'mtime': stat.st_mtime,
                'ctime': stat.st_ctime,
                'mode': stat.st_mode,
                'uid': stat.st_uid if hasattr(stat, 'st_uid') else None,
                'gid': stat.st_gid if hasattr(stat, 'st_gid') else None
            }
        except Exception as e:
            logger.error(f"Failed to get metadata for {filepath}: {e}")
            return {}

    def create_baseline(self):
        """Create baseline of monitored files"""
        logger.info("Creating file integrity baseline...")

        for path in self.config['monitored_paths']:
            if not os.path.exists(path):
                logger.warning(f"Path does not exist: {path}")
                continue

            logger.info(f"Scanning: {path}")

            if os.path.isfile(path):
                self._add_to_baseline(path)
            elif os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for filename in files:
                        filepath = os.path.join(root, filename)
                        self._add_to_baseline(filepath)

        self.stats['files_monitored'] = len(self.baseline)
        logger.info(f"Baseline created: {len(self.baseline)} files")

    def _add_to_baseline(self, filepath: str):
        """Add file to baseline"""
        # Check file extension
        if self.config['file_extensions']:
            ext = os.path.splitext(filepath)[1].lower()
            if ext not in self.config['file_extensions']:
                return

        # Calculate hash and metadata
        file_hash = self.calculate_hash(filepath)
        if not file_hash:
            return

        metadata = self.get_file_metadata(filepath)

        self.baseline[filepath] = {
            'hash': file_hash,
            'metadata': metadata,
            'last_checked': time.time()
        }

    def check_integrity(self):
        """Check files against baseline"""
        logger.info("Checking file integrity...")

        current_files = set()
        changes_found = False

        for path in self.config['monitored_paths']:
            if not os.path.exists(path):
                continue

            if os.path.isfile(path):
                self._check_file(path, current_files)
            elif os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for filename in files:
                        filepath = os.path.join(root, filename)
                        self._check_file(filepath, current_files)

        # Check for deleted files
        baseline_files = set(self.baseline.keys())
        deleted = baseline_files - current_files

        for filepath in deleted:
            self._alert_deleted(filepath)
            changes_found = True

        if not changes_found:
            logger.info("✓ No integrity violations detected")

    def _check_file(self, filepath: str, current_files: Set):
        """Check individual file"""
        current_files.add(filepath)

        # Check file extension
        if self.config['file_extensions']:
            ext = os.path.splitext(filepath)[1].lower()
            if ext not in self.config['file_extensions']:
                return

        # New file
        if filepath not in self.baseline:
            self._alert_new_file(filepath)
            self._add_to_baseline(filepath)
            return

        # Check hash
        current_hash = self.calculate_hash(filepath)
        if not current_hash:
            return

        baseline_hash = self.baseline[filepath]['hash']

        if current_hash != baseline_hash:
            self._alert_modified(filepath, baseline_hash, current_hash)
            # Update baseline
            self.baseline[filepath]['hash'] = current_hash
            self.baseline[filepath]['last_checked'] = time.time()

    def _alert_new_file(self, filepath: str):
        """Generate alert for new file"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': 'NEW_FILE',
            'severity': 'MEDIUM',
            'filepath': filepath,
            'message': f'New file detected: {filepath}',
            'hash': self.calculate_hash(filepath)
        }

        self.alerts.append(alert)
        self.stats['new_files'] += 1
        self.stats['changes_detected'] += 1

        logger.warning(f"[NEW FILE] {filepath}")

    def _alert_modified(self, filepath: str, old_hash: str, new_hash: str):
        """Generate alert for modified file"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': 'MODIFIED_FILE',
            'severity': 'HIGH',
            'filepath': filepath,
            'message': f'File modified: {filepath}',
            'old_hash': old_hash,
            'new_hash': new_hash
        }

        self.alerts.append(alert)
        self.stats['modified_files'] += 1
        self.stats['changes_detected'] += 1

        logger.error(f"[MODIFIED] {filepath}")
        logger.error(f"  Old hash: {old_hash}")
        logger.error(f"  New hash: {new_hash}")

    def _alert_deleted(self, filepath: str):
        """Generate alert for deleted file"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': 'DELETED_FILE',
            'severity': 'HIGH',
            'filepath': filepath,
            'message': f'File deleted: {filepath}',
            'old_hash': self.baseline[filepath]['hash']
        }

        self.alerts.append(alert)
        self.stats['deleted_files'] += 1
        self.stats['changes_detected'] += 1

        logger.error(f"[DELETED] {filepath}")

        # Remove from baseline
        del self.baseline[filepath]

    def save_baseline(self, filepath: str = 'hids_baseline.json'):
        """Save baseline to file"""
        with open(filepath, 'w') as f:
            json.dump(self.baseline, f, indent=2)
        logger.info(f"Baseline saved to {filepath}")

    def load_baseline(self, filepath: str = 'hids_baseline.json'):
        """Load baseline from file"""
        if not os.path.exists(filepath):
            logger.warning(f"Baseline file not found: {filepath}")
            return False

        with open(filepath, 'r') as f:
            self.baseline = json.load(f)

        self.stats['files_monitored'] = len(self.baseline)
        logger.info(f"Baseline loaded: {len(self.baseline)} files")
        return True

    def save_alerts(self, filepath: str = 'hids_alerts.log'):
        """Save alerts to file"""
        with open(filepath, 'a') as f:
            for alert in self.alerts:
                f.write(json.dumps(alert) + '\n')

        logger.info(f"Alerts saved to {filepath}")
        self.alerts = []  # Clear after saving

    def get_stats(self) -> Dict:
        """Get monitoring statistics"""
        return self.stats.copy()

    def print_stats(self):
        """Print statistics"""
        print("\n" + "="*60)
        print("  File Integrity Monitor Statistics")
        print("="*60)
        print(f"Files Monitored:     {self.stats['files_monitored']}")
        print(f"Changes Detected:    {self.stats['changes_detected']}")
        print(f"  New Files:         {self.stats['new_files']}")
        print(f"  Modified Files:    {self.stats['modified_files']}")
        print(f"  Deleted Files:     {self.stats['deleted_files']}")
        print("="*60 + "\n")


def main():
    """Main function for standalone testing"""
    print("="*60)
    print("  HIDS - File Integrity Monitor")
    print("="*60)
    print()

    # Initialize monitor
    monitor = FileIntegrityMonitor()

    # Create test directory
    test_dir = Path('test_fim')
    test_dir.mkdir(exist_ok=True)

    # Override config for testing
    monitor.config['monitored_paths'] = [str(test_dir)]
    monitor.config['file_extensions'] = ['.txt', '.conf']

    # Create test files
    logger.info("Creating test files...")
    (test_dir / 'file1.txt').write_text('Original content 1')
    (test_dir / 'file2.txt').write_text('Original content 2')
    (test_dir / 'config.conf').write_text('setting=value')

    # Create baseline
    monitor.create_baseline()
    monitor.save_baseline('test_baseline.json')

    # Simulate changes
    logger.info("\nSimulating file changes...")
    time.sleep(1)

    # Modify file
    (test_dir / 'file1.txt').write_text('MODIFIED content 1')

    # Add new file
    (test_dir / 'new_file.txt').write_text('New content')

    # Delete file
    (test_dir / 'file2.txt').unlink()

    # Check integrity
    monitor.check_integrity()

    # Save alerts
    monitor.save_alerts('test_hids_alerts.log')

    # Show stats
    monitor.print_stats()

    # Cleanup
    import shutil
    shutil.rmtree(test_dir)
    os.remove('test_baseline.json')
    os.remove('test_hids_alerts.log')

    logger.info("✓ Test completed successfully!")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

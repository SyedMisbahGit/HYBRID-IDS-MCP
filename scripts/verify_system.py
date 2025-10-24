#!/usr/bin/env python3
"""
System Verification Script for Hybrid IDS
Verifies all components are properly configured and working
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path
from typing import List, Tuple

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text: str):
    """Print colored header"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text:^70}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}[OK]{RESET} {text}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}[ERR]{RESET} {text}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}[WARN]{RESET} {text}")


def check_python_version() -> bool:
    """Check Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print_success(f"Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python version: {version.major}.{version.minor}.{version.micro} (need 3.10+)")
        return False


def check_python_packages() -> Tuple[bool, List[str]]:
    """Check required Python packages"""
    required_packages = [
        'numpy',
        'pandas',
        'scipy',
        'sklearn',
        'yaml',
        'zmq',
        'psutil',
        'watchdog',
        'elasticsearch',
        'colorama'
    ]

    missing = []
    for package in required_packages:
        try:
            if package == 'yaml':
                importlib.import_module('yaml')
            elif package == 'zmq':
                importlib.import_module('zmq')
            elif package == 'sklearn':
                importlib.import_module('sklearn')
            else:
                importlib.import_module(package)
            print_success(f"Package {package}: installed")
        except ImportError:
            print_error(f"Package {package}: NOT installed")
            missing.append(package)

    return len(missing) == 0, missing


def check_file_exists(filepath: str) -> bool:
    """Check if file exists"""
    if os.path.exists(filepath):
        print_success(f"File found: {filepath}")
        return True
    else:
        print_error(f"File missing: {filepath}")
        return False


def check_directory_structure() -> bool:
    """Check project directory structure"""
    required_dirs = [
        'src/nids',
        'src/hids',
        'src/integration',
        'src/ai',
        'config',
        'config/hids',
        'config/nids',
        'config/nids/rules',
        'elk',
        'elk/logstash/pipeline',
        'elk/kibana/dashboards',
        'scripts',
        'tests'
    ]

    all_exist = True
    for directory in required_dirs:
        if os.path.isdir(directory):
            print_success(f"Directory found: {directory}")
        else:
            print_error(f"Directory missing: {directory}")
            all_exist = False

    return all_exist


def check_config_files() -> bool:
    """Check configuration files"""
    config_files = [
        'config/hybrid_ids_config.yaml',
        'config/hids/hids_config.yaml',
        'config/nids/nids_config.yaml',
        'config/nids/rules/web_attacks.yaml',
        'config/nids/rules/network_attacks.yaml'
    ]

    all_exist = True
    for config_file in config_files:
        all_exist = check_file_exists(config_file) and all_exist

    return all_exist


def check_source_files() -> bool:
    """Check source code files"""
    source_files = [
        # HIDS
        'src/hids/file_monitor.py',
        'src/hids/process_monitor.py',
        'src/hids/log_analyzer.py',
        'src/hids/hids_main.py',
        # Integration
        'src/integration/unified_alert_manager.py',
        'src/integration/event_correlator.py',
        'src/integration/hybrid_ids.py',
        # NIDS (C++ - check if exist)
        'src/nids/sids.cpp',
        'src/nids/nids.cpp',
        'CMakeLists.txt'
    ]

    all_exist = True
    for source_file in source_files:
        all_exist = check_file_exists(source_file) and all_exist

    return all_exist


def check_documentation() -> bool:
    """Check documentation files"""
    docs = [
        'README.md',
        'INTEGRATION_GUIDE.md',
        'INTEGRATION_QUICKSTART.md',
        'INTEGRATION_COMPLETE.md',
        'HIDS_GUIDE.md',
        'HIDS_QUICKSTART.md',
        'HIDS_COMPLETE.md',
        'NIDS_COMPLETE.md',
        'NIDS_QUICKSTART.md',
        'ARCHITECTURE.md',
        'DEPLOYMENT.md',
        'PROJECT_SUMMARY.md'
    ]

    all_exist = True
    for doc in docs:
        all_exist = check_file_exists(doc) and all_exist

    return all_exist


def check_scripts() -> bool:
    """Check startup scripts"""
    scripts = [
        'scripts/start_hybrid_ids.sh',
        'scripts/start_hybrid_ids.bat',
        'scripts/start_hids.sh',
        'scripts/start_hids.bat',
        'scripts/start_nids.sh',
        'scripts/start_nids.bat'
    ]

    all_exist = True
    for script in scripts:
        all_exist = check_file_exists(script) and all_exist

    return all_exist


def check_nids_build() -> bool:
    """Check if NIDS is built"""
    build_files = [
        'build/sids.exe',  # Windows
        'build/sids',      # Linux/macOS
        'build/Release/sids.exe'  # Windows Release
    ]

    for build_file in build_files:
        if os.path.exists(build_file):
            print_success(f"NIDS build found: {build_file}")
            return True

    print_warning("NIDS not built. Run: mkdir build && cd build && cmake .. && cmake --build .")
    return False


def check_docker() -> bool:
    """Check if Docker is available"""
    try:
        result = subprocess.run(
            ['docker', '--version'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_success(f"Docker: {result.stdout.strip()}")
            return True
        else:
            print_warning("Docker not available (optional for ELK stack)")
            return False
    except FileNotFoundError:
        print_warning("Docker not installed (optional for ELK stack)")
        return False


def check_imports() -> bool:
    """Check if Python modules can be imported"""
    sys.path.insert(0, str(Path('src/integration')))

    try:
        from unified_alert_manager import UnifiedAlertManager, UnifiedAlert
        print_success("unified_alert_manager: imports successfully")

        from event_correlator import EventCorrelator
        print_success("event_correlator: imports successfully")

        return True
    except Exception as e:
        print_error(f"Import error: {e}")
        return False


def run_quick_tests() -> bool:
    """Run quick sanity tests"""
    sys.path.insert(0, str(Path('src/integration')))

    try:
        # Test alert creation
        from unified_alert_manager import UnifiedAlert, AlertSource, AlertSeverity

        alert = UnifiedAlert(
            source=AlertSource.NIDS_SIGNATURE,
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            description="Test"
        )
        print_success("Alert creation: OK")

        # Test alert dict conversion
        alert_dict = alert.to_dict()
        assert 'alert_id' in alert_dict
        assert 'source' in alert_dict
        print_success("Alert serialization: OK")

        # Test correlator initialization
        from event_correlator import EventCorrelator

        config = {'correlation': {'window_seconds': 600}}
        correlator = EventCorrelator(config)
        assert len(correlator.correlation_rules) == 10
        print_success("Correlator initialization: OK")

        return True

    except Exception as e:
        print_error(f"Quick test failed: {e}")
        return False


def main():
    """Main verification function"""
    print_header("HYBRID IDS SYSTEM VERIFICATION")

    results = {}

    # Check Python version
    print_header("1. Python Version")
    results['python_version'] = check_python_version()

    # Check Python packages
    print_header("2. Python Packages")
    results['python_packages'], missing = check_python_packages()
    if missing:
        print(f"\n{YELLOW}To install missing packages:{RESET}")
        print(f"pip install {' '.join(missing)}")

    # Check directory structure
    print_header("3. Directory Structure")
    results['directory_structure'] = check_directory_structure()

    # Check configuration files
    print_header("4. Configuration Files")
    results['config_files'] = check_config_files()

    # Check source files
    print_header("5. Source Code Files")
    results['source_files'] = check_source_files()

    # Check documentation
    print_header("6. Documentation")
    results['documentation'] = check_documentation()

    # Check scripts
    print_header("7. Startup Scripts")
    results['scripts'] = check_scripts()

    # Check NIDS build
    print_header("8. NIDS Build")
    results['nids_build'] = check_nids_build()

    # Check Docker
    print_header("9. Docker (Optional)")
    results['docker'] = check_docker()

    # Check imports
    print_header("10. Python Module Imports")
    results['imports'] = check_imports()

    # Run quick tests
    print_header("11. Quick Sanity Tests")
    results['quick_tests'] = run_quick_tests()

    # Summary
    print_header("VERIFICATION SUMMARY")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    for check, result in results.items():
        status = f"{GREEN}[PASS]{RESET}" if result else f"{RED}[FAIL]{RESET}"
        print(f"{check:30s}: {status}")

    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"Total Checks: {total}")
    print(f"{GREEN}Passed: {passed}{RESET}")
    print(f"{RED}Failed: {failed}{RESET}")

    if failed == 0:
        print(f"\n{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}ALL CHECKS PASSED! System is ready.{RESET}")
        print(f"{GREEN}{'='*70}{RESET}\n")
        return 0
    else:
        print(f"\n{RED}{'='*70}{RESET}")
        print(f"{RED}Some checks failed. Please fix the issues above.{RESET}")
        print(f"{RED}{'='*70}{RESET}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())

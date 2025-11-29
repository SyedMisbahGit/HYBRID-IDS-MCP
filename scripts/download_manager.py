"""
Cross-Platform Dataset Download Manager

Automatically downloads and extracts CIC-IDS2017 and ADFA-LD datasets.
Falls back to manual instructions if automatic download fails.

Supports: Windows, Linux, macOS
"""

import os
import sys
import urllib.request
import zipfile
import tarfile
import hashlib
import platform
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

DATASETS = {
    'CIC-IDS2017': {
        'url': 'https://www.unb.ca/cic/datasets/ids-2017.html',
        'kaggle_url': 'https://www.kaggle.com/datasets/cicdataset/cicids2017',
        'destination': 'data/raw/cicids2017',
        'size': '~7 GB',
        'files': [
            'Monday-WorkingHours.pcap_ISCX.csv',
            'Tuesday-WorkingHours.pcap_ISCX.csv',
            'Wednesday-workingHours.pcap_ISCX.csv',
            'Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv',
            'Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv',
            'Friday-WorkingHours-Morning.pcap_ISCX.csv',
            'Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv',
            'Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv'
        ]
    },
    'ADFA-LD': {
        'url': 'https://www.unsw.adfa.edu.au/australian-centre-for-cyber-security/cybersecurity/ADFA-IDS-Datasets/',
        'destination': 'data/raw/adfa-ld',
        'size': '~500 MB',
        'subdirs': ['Training_Data_Master', 'Attack_Data_Master']
    }
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_success(text):
    """Print success message"""
    print(f"✅ {text}")

def print_error(text):
    """Print error message"""
    print(f"❌ {text}")

def print_warning(text):
    """Print warning message"""
    print(f"⚠️  {text}")

def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")

def get_platform_info():
    """Get platform information"""
    return {
        'system': platform.system(),
        'is_windows': platform.system() == 'Windows',
        'is_linux': platform.system() == 'Linux',
        'is_mac': platform.system() == 'Darwin'
    }

def create_directory(path):
    """Create directory if it doesn't exist"""
    Path(path).mkdir(parents=True, exist_ok=True)
    print_success(f"Created directory: {path}")

def check_dataset_exists(dataset_name):
    """Check if dataset already exists"""
    config = DATASETS[dataset_name]
    dest = config['destination']
    
    if not os.path.exists(dest):
        return False
    
    # Check for CIC-IDS2017 CSV files
    if dataset_name == 'CIC-IDS2017':
        csv_files = [f for f in os.listdir(dest) if f.endswith('.csv')]
        if len(csv_files) >= 1:  # At least one CSV file
            print_info(f"{dataset_name} found: {len(csv_files)} CSV files")
            return True
    
    # Check for ADFA-LD directories
    elif dataset_name == 'ADFA-LD':
        training_dir = os.path.join(dest, 'Training_Data_Master')
        attack_dir = os.path.join(dest, 'Attack_Data_Master')
        if os.path.exists(training_dir) and os.path.exists(attack_dir):
            print_info(f"{dataset_name} found")
            return True
    
    return False

# ============================================================================
# DOWNLOAD FUNCTIONS
# ============================================================================

def download_file(url, destination, chunk_size=8192):
    """
    Download file with progress indication
    
    Note: This is a basic implementation. For large files,
    consider using libraries like requests with tqdm for progress bars.
    """
    try:
        print_info(f"Downloading from: {url}")
        print_info(f"Destination: {destination}")
        
        # Create destination directory
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        # Download file
        urllib.request.urlretrieve(url, destination)
        print_success(f"Downloaded: {destination}")
        return True
    
    except Exception as e:
        print_error(f"Download failed: {e}")
        return False

def extract_archive(archive_path, destination):
    """Extract zip or tar archive"""
    try:
        print_info(f"Extracting: {archive_path}")
        
        if archive_path.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(destination)
        elif archive_path.endswith(('.tar.gz', '.tgz')):
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                tar_ref.extractall(destination)
        elif archive_path.endswith('.tar'):
            with tarfile.open(archive_path, 'r') as tar_ref:
                tar_ref.extractall(destination)
        else:
            print_error(f"Unsupported archive format: {archive_path}")
            return False
        
        print_success(f"Extracted to: {destination}")
        return True
    
    except Exception as e:
        print_error(f"Extraction failed: {e}")
        return False

# ============================================================================
# DATASET-SPECIFIC FUNCTIONS
# ============================================================================

def download_cicids2017():
    """Attempt to download CIC-IDS2017"""
    print_header("CIC-IDS2017 Download")
    
    config = DATASETS['CIC-IDS2017']
    
    # Check if already exists
    if check_dataset_exists('CIC-IDS2017'):
        print_success("CIC-IDS2017 already exists!")
        return True
    
    # Create destination directory
    create_directory(config['destination'])
    
    # Automatic download is difficult for CIC-IDS2017 due to:
    # 1. No direct download link (requires form submission)
    # 2. Large file size (7GB)
    # 3. Kaggle requires authentication
    
    print_warning("Automatic download not available for CIC-IDS2017")
    print_manual_instructions_cicids2017()
    return False

def print_manual_instructions_cicids2017():
    """Print manual download instructions for CIC-IDS2017"""
    config = DATASETS['CIC-IDS2017']
    
    print("\n" + "-"*70)
    print("📥 MANUAL DOWNLOAD REQUIRED")
    print("-"*70)
    print(f"\n1. Visit one of these URLs:")
    print(f"   Primary: {config['url']}")
    print(f"   Mirror:  {config['kaggle_url']}")
    print(f"\n2. Download the CSV files (8 files, {config['size']} total)")
    print(f"\n3. Place all CSV files in:")
    print(f"   {os.path.abspath(config['destination'])}")
    print(f"\n4. Expected files:")
    for i, filename in enumerate(config['files'], 1):
        print(f"   {i}. {filename}")
    print("\n" + "-"*70)

def download_adfa_ld():
    """Attempt to download ADFA-LD"""
    print_header("ADFA-LD Download")
    
    config = DATASETS['ADFA-LD']
    
    # Check if already exists
    if check_dataset_exists('ADFA-LD'):
        print_success("ADFA-LD already exists!")
        return True
    
    # Create destination directory
    create_directory(config['destination'])
    
    # Automatic download is difficult for ADFA-LD due to:
    # 1. No direct download link
    # 2. Requires manual navigation
    
    print_warning("Automatic download not available for ADFA-LD")
    print_manual_instructions_adfa_ld()
    return False

def print_manual_instructions_adfa_ld():
    """Print manual download instructions for ADFA-LD"""
    config = DATASETS['ADFA-LD']
    
    print("\n" + "-"*70)
    print("📥 MANUAL DOWNLOAD REQUIRED")
    print("-"*70)
    print(f"\n1. Visit: {config['url']}")
    print(f"\n2. Download ADFA-LD dataset ({config['size']})")
    print(f"\n3. Extract the archive to:")
    print(f"   {os.path.abspath(config['destination'])}")
    print(f"\n4. Expected directory structure:")
    print(f"   {config['destination']}/")
    for subdir in config['subdirs']:
        print(f"   ├── {subdir}/")
    print("\n" + "-"*70)

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main download manager"""
    print_header("🛡️  Hybrid IDS - Dataset Download Manager")
    
    # Get platform info
    platform_info = get_platform_info()
    print_info(f"Platform: {platform_info['system']}")
    
    # Check data directory
    if not os.path.exists('data'):
        print_info("Creating data directory structure...")
        create_directory('data/raw')
        create_directory('data/mock')
        create_directory('data/processed')
    
    print("\n" + "="*70)
    print("  DATASET DOWNLOAD OPTIONS")
    print("="*70)
    print("\n1. CIC-IDS2017 (Network Traffic)")
    print("2. ADFA-LD (System Call Traces)")
    print("3. Both")
    print("4. Skip (use mock data)")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == '1':
        download_cicids2017()
    elif choice == '2':
        download_adfa_ld()
    elif choice == '3':
        download_cicids2017()
        download_adfa_ld()
    elif choice == '4':
        print_info("Skipping dataset download")
        print_info("You can generate mock data with: python utils/mock_generator.py")
    else:
        print_error("Invalid choice")
        return
    
    print("\n" + "="*70)
    print("  NEXT STEPS")
    print("="*70)
    print("\nAfter downloading datasets:")
    print("1. Verify files are in correct locations")
    print("2. Run: python quick_start.py")
    print("3. Train models: python src/ml/nids/sids_trainer.py")
    print("4. Launch dashboard: python dashboard/app.py")
    print("\nOr use mock data for testing:")
    print("  python utils/mock_generator.py")
    print("="*70)

if __name__ == "__main__":
    main()

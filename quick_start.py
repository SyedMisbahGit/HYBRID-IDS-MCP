"""
Quick Start Script for Hybrid IDS ML Demo

This script helps you get started quickly by:
1. Checking dependencies
2. Verifying dataset locations
3. Providing training commands
4. Launching the dashboard
"""

import os
import sys
import subprocess
import importlib.util

def check_python_version():
    """Check if Python version is 3.10+"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Need 3.10+")
        return False

def check_package(package_name):
    """Check if a package is installed"""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def check_dependencies():
    """Check if required packages are installed"""
    print("\nChecking dependencies...")
    
    required_packages = {
        'ML Pipeline': ['numpy', 'pandas', 'sklearn', 'tensorflow', 'joblib'],
        'Dashboard': ['streamlit', 'plotly']
    }
    
    all_installed = True
    
    for category, packages in required_packages.items():
        print(f"\n{category}:")
        for package in packages:
            if check_package(package):
                print(f"  ✅ {package}")
            else:
                print(f"  ❌ {package} - NOT INSTALLED")
                all_installed = False
    
    return all_installed

def check_datasets():
    """Check if datasets are downloaded"""
    print("\nChecking datasets...")
    
    datasets = {
        'CIC-IDS2017': 'data/raw/cicids2017',
        'ADFA-LD': 'data/raw/adfa-ld'
    }
    
    datasets_found = {}
    
    for name, path in datasets.items():
        if os.path.exists(path) and os.listdir(path):
            print(f"✅ {name} found at {path}")
            datasets_found[name] = True
        else:
            print(f"❌ {name} not found at {path}")
            datasets_found[name] = False
    
    return datasets_found

def check_models():
    """Check if models are trained"""
    print("\nChecking trained models...")
    
    models = {
        'NIDS SIDS': 'models/nids/sids_rf.pkl',
        'NIDS A-IDS': 'models/nids/aids_iforest.pkl',
        'HIDS LSTM': 'models/hids/lstm_autoencoder.h5'
    }
    
    models_found = {}
    
    for name, path in models.items():
        if os.path.exists(path):
            print(f"✅ {name} trained")
            models_found[name] = True
        else:
            print(f"❌ {name} not trained")
            models_found[name] = False
    
    return models_found

def print_next_steps(deps_ok, datasets, models):
    """Print next steps based on current state"""
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    
    if not deps_ok:
        print("\n1. Install dependencies:")
        print("   pip install -r src/ml/requirements.txt")
        print("   pip install -r dashboard/requirements.txt")
        return
    
    if not any(datasets.values()):
        print("\n1. Download datasets:")
        print("\n   CIC-IDS2017 (~7GB):")
        print("   https://www.unb.ca/cic/datasets/ids-2017.html")
        print("   Extract CSV files to: data/raw/cicids2017/")
        print("\n   ADFA-LD (~500MB):")
        print("   https://www.unsw.adfa.edu.au/australian-centre-for-cyber-security/cybersecurity/ADFA-IDS-Datasets/")
        print("   Extract to: data/raw/adfa-ld/")
        return
    
    if not any(models.values()):
        print("\n1. Train models:")
        if datasets.get('CIC-IDS2017'):
            print("\n   NIDS SIDS (Random Forest):")
            print("   cd src/ml/nids")
            print("   python sids_trainer.py")
            print("\n   NIDS A-IDS (Isolation Forest):")
            print("   python aids_trainer.py")
        
        if datasets.get('ADFA-LD'):
            print("\n   HIDS (LSTM Autoencoder):")
            print("   cd src/ml/hids")
            print("   python sequence_trainer.py")
        return
    
    print("\n✅ Everything is ready!")
    print("\n1. Launch dashboard:")
    print("   streamlit run dashboard/app.py")
    print("\n2. Open browser to: http://localhost:8501")
    print("\n3. Enable 'Simulation Mode' in sidebar")
    print("\n4. Enjoy the demo!")

def main():
    """Main function"""
    print("="*60)
    print("Hybrid IDS - ML Demo Quick Start")
    print("="*60)
    
    # Check Python version
    if not check_python_version():
        print("\n❌ Please upgrade to Python 3.10 or higher")
        return
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    # Check datasets
    datasets = check_datasets()
    
    # Check models
    models = check_models()
    
    # Print next steps
    print_next_steps(deps_ok, datasets, models)
    
    print("\n" + "="*60)
    print("For detailed instructions, see: README_ML_DEMO.md")
    print("="*60)

if __name__ == "__main__":
    main()

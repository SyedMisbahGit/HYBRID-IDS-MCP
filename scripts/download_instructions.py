"""
Dataset Download Instructions

Provides detailed instructions for downloading and setting up
the CIC-IDS2017 and ADFA-LD datasets.
"""

import os


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def print_cicids2017_instructions():
    """Print CIC-IDS2017 download instructions"""
    print_header("📥 CIC-IDS2017 Dataset (Network Traffic)")
    
    print("\n📊 Dataset Information:")
    print("  • Size: ~7 GB (CSV files)")
    print("  • Samples: 2.8 million network flows")
    print("  • Features: 78 CIC flow features")
    print("  • Labels: BENIGN + 14 attack types")
    print("  • Source: Canadian Institute for Cybersecurity")
    
    print("\n🔗 Download Links:")
    print("  Primary: https://www.unb.ca/cic/datasets/ids-2017.html")
    print("  Mirror: https://www.kaggle.com/datasets/cicdataset/cicids2017")
    
    print("\n📝 Download Steps:")
    print("  1. Visit the URL above")
    print("  2. Download the CSV files (Monday-Friday traffic)")
    print("  3. You will get files like:")
    print("     - Monday-WorkingHours.pcap_ISCX.csv")
    print("     - Tuesday-WorkingHours.pcap_ISCX.csv")
    print("     - Wednesday-workingHours.pcap_ISCX.csv")
    print("     - Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv")
    print("     - Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv")
    print("     - Friday-WorkingHours-Morning.pcap_ISCX.csv")
    print("     - Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv")
    print("     - Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv")
    
    print("\n📁 Installation:")
    target_dir = os.path.abspath("data/raw/cicids2017")
    print(f"  Place all CSV files in: {target_dir}")
    print("\n  Directory structure should be:")
    print("    data/raw/cicids2017/")
    print("    ├── Monday-WorkingHours.pcap_ISCX.csv")
    print("    ├── Tuesday-WorkingHours.pcap_ISCX.csv")
    print("    ├── Wednesday-workingHours.pcap_ISCX.csv")
    print("    └── ... (other CSV files)")
    
    print("\n✅ Verification:")
    print("  After placing files, run:")
    print("    python -c \"import os; print(len([f for f in os.listdir('data/raw/cicids2017') if f.endswith('.csv')]))\"")
    print("  Expected output: 8 (or more CSV files)")


def print_adfa_ld_instructions():
    """Print ADFA-LD download instructions"""
    print_header("📥 ADFA-LD Dataset (System Call Traces)")
    
    print("\n📊 Dataset Information:")
    print("  • Size: ~500 MB")
    print("  • Samples: 833 normal traces + 746 attack traces")
    print("  • Format: Text files with system call sequences")
    print("  • Attack Types: 6 categories")
    print("  • Source: UNSW Canberra (Australian Defence Force Academy)")
    
    print("\n🔗 Download Link:")
    print("  https://www.unsw.adfa.edu.au/australian-centre-for-cyber-security/cybersecurity/ADFA-IDS-Datasets/")
    
    print("\n📝 Download Steps:")
    print("  1. Visit the URL above")
    print("  2. Download 'ADFA-LD' (Linux Dataset)")
    print("  3. You will get a compressed file (e.g., ADFA-LD.tar.gz or ADFA-LD.zip)")
    print("  4. Extract the archive")
    
    print("\n📁 Installation:")
    target_dir = os.path.abspath("data/raw/adfa-ld")
    print(f"  Extract contents to: {target_dir}")
    print("\n  Directory structure should be:")
    print("    data/raw/adfa-ld/")
    print("    ├── Training_Data_Master/")
    print("    │   ├── U0001")
    print("    │   ├── U0002")
    print("    │   └── ... (833 files)")
    print("    └── Attack_Data_Master/")
    print("        ├── U0001")
    print("        ├── U0002")
    print("        └── ... (746 files)")
    
    print("\n✅ Verification:")
    print("  After extracting, run:")
    print("    python -c \"import os; print(len(os.listdir('data/raw/adfa-ld/Training_Data_Master')))\"")
    print("  Expected output: 833 (normal traces)")


def print_alternative_options():
    """Print alternative options"""
    print_header("🔄 Alternative Options")
    
    print("\n1️⃣  Use Mock Data (For Testing Only):")
    print("  Generate synthetic data to test the pipeline:")
    print("    python utils/mock_generator.py")
    print("\n  ⚠️  WARNING: Models trained on mock data will have random accuracy!")
    print("  Use this ONLY to verify the code works, not for real results.")
    
    print("\n2️⃣  Use Smaller Subsets:")
    print("  If storage is limited, you can:")
    print("  • Download only 1-2 days of CIC-IDS2017 (instead of all 8 files)")
    print("  • Use a subset of ADFA-LD traces")
    print("  • Models will still train, but with less data")
    
    print("\n3️⃣  Use Cloud Storage:")
    print("  • Download datasets to Google Drive / Dropbox")
    print("  • Create symlinks to data/raw/ directories")
    print("  • Keeps your repo clean while accessing large files")


def print_next_steps():
    """Print next steps after download"""
    print_header("🚀 Next Steps After Download")
    
    print("\n1. Verify data is in correct location:")
    print("     python quick_start.py")
    
    print("\n2. Train NIDS models:")
    print("     cd src/ml/nids")
    print("     python sids_trainer.py")
    print("     python aids_trainer.py")
    
    print("\n3. Train HIDS model:")
    print("     cd src/ml/hids")
    print("     python sequence_trainer.py")
    
    print("\n4. Launch dashboard:")
    print("     streamlit run dashboard/app.py")


def main():
    """Main function"""
    print("\n" + "="*70)
    print("  🛡️  HYBRID IDS - DATASET DOWNLOAD INSTRUCTIONS")
    print("="*70)
    
    print("\n📌 You need TWO datasets to train the ML models:")
    print("  1. CIC-IDS2017 (for Network IDS)")
    print("  2. ADFA-LD (for Host IDS)")
    
    # CIC-IDS2017 instructions
    print_cicids2017_instructions()
    
    # ADFA-LD instructions
    print_adfa_ld_instructions()
    
    # Alternative options
    print_alternative_options()
    
    # Next steps
    print_next_steps()
    
    print("\n" + "="*70)
    print("  📚 For more information, see: README_ML_DEMO.md")
    print("="*70)
    print()


if __name__ == "__main__":
    main()

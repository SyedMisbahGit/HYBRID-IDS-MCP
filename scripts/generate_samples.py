"""
Sample Data Generator

Creates small sample datasets for testing without downloading full datasets.
Useful for quick testing and development.
"""

import numpy as np
import pandas as pd
import os
import json

def generate_nids_sample(num_samples=1000, output_path='data/samples/nids_test_sample.csv'):
    """
    Generate sample network traffic data mimicking CIC-IDS2017 format
    
    Args:
        num_samples: Number of samples to generate
        output_path: Output CSV file path
    """
    print(f"Generating {num_samples} NIDS samples...")
    
    # Create output directory
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Define 78 CIC features (simplified names)
    feature_names = [
        'Flow Duration', 'Total Fwd Packets', 'Total Backward Packets',
        'Total Length of Fwd Packets', 'Total Length of Bwd Packets',
        'Fwd Packet Length Max', 'Fwd Packet Length Min', 'Fwd Packet Length Mean',
        'Bwd Packet Length Max', 'Bwd Packet Length Min', 'Bwd Packet Length Mean',
        'Flow Bytes/s', 'Flow Packets/s', 'Flow IAT Mean', 'Flow IAT Std',
        'Fwd IAT Total', 'Fwd IAT Mean', 'Fwd IAT Std', 'Fwd IAT Max', 'Fwd IAT Min',
        'Bwd IAT Total', 'Bwd IAT Mean', 'Bwd IAT Std', 'Bwd IAT Max', 'Bwd IAT Min',
        'Fwd PSH Flags', 'Bwd PSH Flags', 'Fwd URG Flags', 'Bwd URG Flags',
        'Fwd Header Length', 'Bwd Header Length', 'Fwd Packets/s', 'Bwd Packets/s',
        'Min Packet Length', 'Max Packet Length', 'Packet Length Mean', 'Packet Length Std',
        'Packet Length Variance', 'FIN Flag Count', 'SYN Flag Count', 'RST Flag Count',
        'PSH Flag Count', 'ACK Flag Count', 'URG Flag Count', 'CWE Flag Count',
        'ECE Flag Count', 'Down/Up Ratio', 'Average Packet Size', 'Avg Fwd Segment Size',
        'Avg Bwd Segment Size', 'Fwd Avg Bytes/Bulk', 'Fwd Avg Packets/Bulk',
        'Fwd Avg Bulk Rate', 'Bwd Avg Bytes/Bulk', 'Bwd Avg Packets/Bulk',
        'Bwd Avg Bulk Rate', 'Subflow Fwd Packets', 'Subflow Fwd Bytes',
        'Subflow Bwd Packets', 'Subflow Bwd Bytes', 'Init_Win_bytes_forward',
        'Init_Win_bytes_backward', 'act_data_pkt_fwd', 'min_seg_size_forward',
        'Active Mean', 'Active Std', 'Active Max', 'Active Min',
        'Idle Mean', 'Idle Std', 'Idle Max', 'Idle Min',
        'Protocol', 'Source Port', 'Destination Port', 'Timestamp',
        'Flow ID', 'Source IP', 'Destination IP'
    ]
    
    # Generate random data
    data = {}
    
    # Numeric features (first 71 features)
    for i, feature in enumerate(feature_names[:71]):
        if 'Flag' in feature or 'Count' in feature:
            # Binary or count features
            data[feature] = np.random.randint(0, 10, num_samples)
        elif 'Ratio' in feature:
            # Ratio features
            data[feature] = np.random.uniform(0, 1, num_samples)
        else:
            # Continuous features
            data[feature] = np.random.randn(num_samples) * 1000 + 5000
    
    # Protocol (TCP=6, UDP=17, ICMP=1)
    data['Protocol'] = np.random.choice([6, 17, 1], num_samples, p=[0.7, 0.2, 0.1])
    
    # Ports
    data['Source Port'] = np.random.randint(1024, 65535, num_samples)
    data['Destination Port'] = np.random.choice([80, 443, 22, 21, 3389, 445], num_samples)
    
    # Timestamp
    data['Timestamp'] = pd.date_range(start='2024-01-01', periods=num_samples, freq='1S')
    
    # Flow ID
    data['Flow ID'] = [f"flow_{i}" for i in range(num_samples)]
    
    # IPs
    data['Source IP'] = [f"192.168.1.{np.random.randint(1, 255)}" for _ in range(num_samples)]
    data['Destination IP'] = [f"10.0.0.{np.random.randint(1, 255)}" for _ in range(num_samples)]
    
    # Labels (80% benign, 20% attacks)
    attack_types = ['BENIGN', 'DoS', 'DDoS', 'PortScan', 'BruteForce', 'WebAttack']
    data['Label'] = np.random.choice(
        attack_types,
        num_samples,
        p=[0.8, 0.05, 0.05, 0.04, 0.03, 0.03]
    )
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"✅ Saved {num_samples} samples to {output_path}")
    
    # Print statistics
    print(f"\nLabel distribution:")
    print(df['Label'].value_counts())
    
    return df

def generate_hids_sample(num_sequences=100, sequence_length=100, output_path='data/samples/hids_test_sample.csv'):
    """
    Generate sample system call sequences mimicking ADFA-LD format
    
    Args:
        num_sequences: Number of sequences to generate
        sequence_length: Length of each sequence
        output_path: Output CSV file path
    """
    print(f"\nGenerating {num_sequences} HIDS sequences...")
    
    # Create output directory
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Common Linux system calls (simplified)
    common_syscalls = [
        1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
        21, 22, 33, 39, 41, 45, 54, 56, 59, 60, 61, 62, 63, 78, 79, 80,
        89, 90, 102, 104, 107, 120, 125, 140, 158, 186, 191, 192, 195, 197
    ]
    
    data = []
    
    for i in range(num_sequences):
        # 80% normal, 20% attack
        is_attack = np.random.random() < 0.2
        
        if is_attack:
            # Attack sequences have more rare syscalls
            rare_syscalls = [200, 201, 202, 203, 204, 205, 206, 207, 208, 209]
            syscalls = np.random.choice(
                common_syscalls + rare_syscalls,
                sequence_length,
                p=[0.015] * len(common_syscalls) + [0.05] * len(rare_syscalls)
            )
            label = 1
        else:
            # Normal sequences use common syscalls
            syscalls = np.random.choice(common_syscalls, sequence_length)
            label = 0
        
        data.append({
            'sequence_id': i,
            'syscalls': ' '.join(map(str, syscalls)),
            'label': label
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"✅ Saved {num_sequences} sequences to {output_path}")
    
    # Print statistics
    print(f"\nLabel distribution:")
    print(f"Normal: {(df['label'] == 0).sum()}")
    print(f"Attack: {(df['label'] == 1).sum()}")
    
    return df

def create_readme():
    """Create README for sample data"""
    readme_content = """# Sample Data

This directory contains sample datasets for testing the Hybrid IDS ML Demo without downloading full datasets.

## Files

### NIDS Sample (`nids_test_sample.csv`)
- 1,000 network traffic samples
- 78 CIC-IDS2017 features
- Labels: Benign, DoS, DDoS, PortScan, BruteForce, WebAttack
- Distribution: 80% benign, 20% attacks

### HIDS Sample (`hids_test_sample.csv`)
- 100 system call sequences
- 100 syscalls per sequence
- Labels: 0 (normal), 1 (attack)
- Distribution: 80% normal, 20% attack

## Usage

These samples are for **testing only**. For production use, download full datasets:
- CIC-IDS2017: https://www.unb.ca/cic/datasets/ids-2017.html
- ADFA-LD: https://www.unsw.adfa.edu.au/australian-centre-for-cyber-security/cybersecurity/ADFA-IDS-Datasets/

## Generation

Samples were generated using `scripts/generate_samples.py`:

```bash
python scripts/generate_samples.py
```
"""
    
    readme_path = 'data/samples/README.md'
    os.makedirs(os.path.dirname(readme_path), exist_ok=True)
    
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    print(f"\n✅ Created README at {readme_path}")

def main():
    """Main function"""
    print("="*60)
    print("Sample Data Generator for Hybrid IDS")
    print("="*60)
    
    # Generate NIDS sample
    generate_nids_sample(num_samples=1000)
    
    # Generate HIDS sample
    generate_hids_sample(num_sequences=100)
    
    # Create README
    create_readme()
    
    print("\n" + "="*60)
    print("✅ Sample data generation complete!")
    print("="*60)
    print("\nYou can now test the ML pipeline with these samples.")
    print("Note: For production use, download full datasets.")

if __name__ == "__main__":
    main()

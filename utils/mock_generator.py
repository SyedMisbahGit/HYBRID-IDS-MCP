"""
Mock Data Generator for Testing

Generates lightweight, synthetic datasets that mimic the structure of:
- CIC-IDS2017 (for NIDS)
- ADFA-LD (for HIDS)

This allows testing the ML pipeline without downloading 7GB+ of real data.
"""

import os
import numpy as np
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockDataGenerator:
    """Generate mock datasets for testing"""
    
    @staticmethod
    def generate_cicids2017_mock(output_dir='data/mock/cicids2017', num_samples=1000):
        """
        Generate mock CIC-IDS2017 dataset
        
        Args:
            output_dir: Directory to save mock CSV
            num_samples: Number of samples to generate
            
        Returns:
            Path to generated CSV file
        """
        logger.info(f"Generating mock CIC-IDS2017 dataset ({num_samples} samples)...")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # CIC-IDS2017 feature names (78 features + metadata)
        # These are the actual column names from the real dataset
        feature_names = [
            ' Destination Port', ' Flow Duration', ' Total Fwd Packets',
            ' Total Backward Packets', 'Total Length of Fwd Packets',
            ' Total Length of Bwd Packets', ' Fwd Packet Length Max',
            ' Fwd Packet Length Min', ' Fwd Packet Length Mean',
            ' Fwd Packet Length Std', 'Bwd Packet Length Max',
            ' Bwd Packet Length Min', ' Bwd Packet Length Mean',
            ' Bwd Packet Length Std', 'Flow Bytes/s', ' Flow Packets/s',
            ' Flow IAT Mean', ' Flow IAT Std', ' Flow IAT Max', ' Flow IAT Min',
            'Fwd IAT Total', ' Fwd IAT Mean', ' Fwd IAT Std', ' Fwd IAT Max',
            ' Fwd IAT Min', 'Bwd IAT Total', ' Bwd IAT Mean', ' Bwd IAT Std',
            ' Bwd IAT Max', ' Bwd IAT Min', 'Fwd PSH Flags', ' Bwd PSH Flags',
            ' Fwd URG Flags', ' Bwd URG Flags', ' Fwd Header Length',
            ' Bwd Header Length', 'Fwd Packets/s', ' Bwd Packets/s',
            ' Min Packet Length', ' Max Packet Length', ' Packet Length Mean',
            ' Packet Length Std', ' Packet Length Variance', 'FIN Flag Count',
            ' SYN Flag Count', ' RST Flag Count', ' PSH Flag Count',
            ' ACK Flag Count', ' URG Flag Count', ' CWE Flag Count',
            ' ECE Flag Count', ' Down/Up Ratio', ' Average Packet Size',
            ' Avg Fwd Segment Size', ' Avg Bwd Segment Size',
            'Fwd Header Length.1', ' Fwd Avg Bytes/Bulk', ' Fwd Avg Packets/Bulk',
            ' Fwd Avg Bulk Rate', ' Bwd Avg Bytes/Bulk', ' Bwd Avg Packets/Bulk',
            ' Bwd Avg Bulk Rate', 'Subflow Fwd Packets', ' Subflow Fwd Bytes',
            ' Subflow Bwd Packets', ' Subflow Bwd Bytes',
            ' Init_Win_bytes_forward', ' Init_Win_bytes_backward',
            ' act_data_pkt_fwd', ' min_seg_size_forward', 'Active Mean',
            ' Active Std', ' Active Max', ' Active Min', 'Idle Mean',
            ' Idle Std', ' Idle Max', ' Idle Min', ' Label'
        ]
        
        # Generate random data
        data = {}
        
        # Numeric features (first 77 features)
        for feature in feature_names[:-1]:
            if 'Flag' in feature or 'Count' in feature:
                # Binary or count features (0-10)
                data[feature] = np.random.randint(0, 10, num_samples)
            elif 'Ratio' in feature:
                # Ratio features (0-1)
                data[feature] = np.random.uniform(0, 1, num_samples)
            elif 'Port' in feature:
                # Port numbers
                data[feature] = np.random.choice([80, 443, 22, 21, 3389, 445, 8080], num_samples)
            else:
                # Continuous features (normal distribution)
                data[feature] = np.abs(np.random.randn(num_samples) * 1000 + 5000)
        
        # Labels (80% BENIGN, 20% attacks)
        attack_types = ['BENIGN', 'DoS', 'DDoS', 'PortScan', 'Bot', 'Web Attack', 'Infiltration']
        data[' Label'] = np.random.choice(
            attack_types,
            num_samples,
            p=[0.80, 0.05, 0.04, 0.04, 0.03, 0.02, 0.02]
        )
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Save to CSV
        output_file = os.path.join(output_dir, 'mock_cicids2017.csv')
        df.to_csv(output_file, index=False)
        
        logger.info(f"[SUCCESS] Generated mock CIC-IDS2017: {output_file}")
        logger.info(f"   Samples: {num_samples}")
        logger.info(f"   Features: {len(feature_names) - 1}")
        logger.info(f"   Label distribution:\n{df[' Label'].value_counts()}")
        
        return output_file
    
    @staticmethod
    def generate_adfa_ld_mock(output_dir='data/mock/adfa-ld', num_normal=100, num_attack=50):
        """
        Generate mock ADFA-LD dataset
        
        Args:
            output_dir: Directory to save mock traces
            num_normal: Number of normal traces
            num_attack: Number of attack traces
            
        Returns:
            Tuple of (training_dir, attack_dir)
        """
        logger.info(f"Generating mock ADFA-LD dataset...")
        logger.info(f"   Normal traces: {num_normal}")
        logger.info(f"   Attack traces: {num_attack}")
        
        # Create directories
        training_dir = os.path.join(output_dir, 'Training_Data_Master')
        attack_dir = os.path.join(output_dir, 'Attack_Data_Master')
        os.makedirs(training_dir, exist_ok=True)
        os.makedirs(attack_dir, exist_ok=True)
        
        # Common Linux system calls (realistic syscall numbers)
        common_syscalls = [
            1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
            21, 22, 33, 39, 41, 45, 54, 56, 59, 60, 61, 62, 63, 78, 79, 80,
            89, 90, 102, 104, 107, 120, 125, 140, 158, 186, 191, 192, 195, 197
        ]
        
        # Generate normal traces
        for i in range(num_normal):
            # Normal traces: 500-2000 syscalls, mostly common ones
            trace_length = np.random.randint(500, 2000)
            syscalls = np.random.choice(common_syscalls, trace_length)
            
            # Save to file
            filename = f"U{i+1:04d}"
            filepath = os.path.join(training_dir, filename)
            with open(filepath, 'w') as f:
                f.write(' '.join(map(str, syscalls)))
        
        # Generate attack traces
        rare_syscalls = [200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210]
        
        for i in range(num_attack):
            # Attack traces: more rare syscalls, different patterns
            trace_length = np.random.randint(300, 1500)
            
            # Mix common and rare syscalls (30% rare for attacks)
            all_syscalls = common_syscalls + rare_syscalls
            probs = [0.014] * len(common_syscalls) + [0.03] * len(rare_syscalls)
            probs = np.array(probs) / sum(probs)  # Normalize
            
            syscalls = np.random.choice(all_syscalls, trace_length, p=probs)
            
            # Save to file
            filename = f"U{i+1:04d}"
            filepath = os.path.join(attack_dir, filename)
            with open(filepath, 'w') as f:
                f.write(' '.join(map(str, syscalls)))
        
        logger.info(f"[SUCCESS] Generated mock ADFA-LD:")
        logger.info(f"   Training dir: {training_dir} ({num_normal} files)")
        logger.info(f"   Attack dir: {attack_dir} ({num_attack} files)")
        
        return training_dir, attack_dir
    
    @staticmethod
    def get_cicids_feature_names():
        """Get list of CIC-IDS2017 feature names"""
        return [
            ' Destination Port', ' Flow Duration', ' Total Fwd Packets',
            ' Total Backward Packets', 'Total Length of Fwd Packets',
            ' Total Length of Bwd Packets', ' Fwd Packet Length Max',
            ' Fwd Packet Length Min', ' Fwd Packet Length Mean',
            ' Fwd Packet Length Std', 'Bwd Packet Length Max',
            ' Bwd Packet Length Min', ' Bwd Packet Length Mean',
            ' Bwd Packet Length Std', 'Flow Bytes/s', ' Flow Packets/s',
            ' Flow IAT Mean', ' Flow IAT Std', ' Flow IAT Max', ' Flow IAT Min',
            'Fwd IAT Total', ' Fwd IAT Mean', ' Fwd IAT Std', ' Fwd IAT Max',
            ' Fwd IAT Min', 'Bwd IAT Total', ' Bwd IAT Mean', ' Bwd IAT Std',
            ' Bwd IAT Max', ' Bwd IAT Min', 'Fwd PSH Flags', ' Bwd PSH Flags',
            ' Fwd URG Flags', ' Bwd URG Flags', ' Fwd Header Length',
            ' Bwd Header Length', 'Fwd Packets/s', ' Bwd Packets/s',
            ' Min Packet Length', ' Max Packet Length', ' Packet Length Mean',
            ' Packet Length Std', ' Packet Length Variance', 'FIN Flag Count',
            ' SYN Flag Count', ' RST Flag Count', ' PSH Flag Count',
            ' ACK Flag Count', ' URG Flag Count', ' CWE Flag Count',
            ' ECE Flag Count', ' Down/Up Ratio', ' Average Packet Size',
            ' Avg Fwd Segment Size', ' Avg Bwd Segment Size',
            'Fwd Header Length.1', ' Fwd Avg Bytes/Bulk', ' Fwd Avg Packets/Bulk',
            ' Fwd Avg Bulk Rate', ' Bwd Avg Bytes/Bulk', ' Bwd Avg Packets/Bulk',
            ' Bwd Avg Bulk Rate', 'Subflow Fwd Packets', ' Subflow Fwd Bytes',
            ' Subflow Bwd Packets', ' Subflow Bwd Bytes',
            ' Init_Win_bytes_forward', ' Init_Win_bytes_backward',
            ' act_data_pkt_fwd', ' min_seg_size_forward', 'Active Mean',
            ' Active Std', ' Active Max', ' Active Min', 'Idle Mean',
            ' Idle Std', ' Idle Max', ' Idle Min'
        ]

    @staticmethod
    def generate_single_sample(attack_type='BENIGN', intensity='Medium'):
        """
        Generate a single feature sample for real-time simulation
        
        Args:
            attack_type: 'BENIGN', 'DDoS', 'PortScan', 'BruteForce'
            intensity: 'Low', 'Medium', 'High'
            
        Returns:
            DataFrame with 1 row and 78 features
        """
        feature_names = MockDataGenerator.get_cicids_feature_names()
        data = {}
        
        # Base multipliers based on intensity
        multiplier = 1.0
        if intensity == 'Low': multiplier = 0.5
        elif intensity == 'High': multiplier = 2.0
        
        # Generate base random data (Normal-ish)
        for feature in feature_names:
            if 'Port' in feature:
                data[feature] = [np.random.choice([80, 443, 22, 53])]
            elif 'Flag' in feature or 'Count' in feature:
                data[feature] = [0]
            else:
                data[feature] = [np.abs(np.random.randn() * 100)]
        
        # Inject Attack Patterns
        if attack_type == 'DDoS':
            # High packet count, small duration, high bytes/sec
            data[' Total Fwd Packets'] = [np.random.randint(1000, 5000) * multiplier]
            data[' Flow Duration'] = [np.random.randint(100, 1000)]
            data['Flow Bytes/s'] = [np.random.randint(100000, 1000000) * multiplier]
            data[' Fwd Packet Length Max'] = [1000 * multiplier]
            
        elif attack_type == 'PortScan':
            # Many ports (handled by logic outside, but features show short flows)
            data[' Flow Duration'] = [np.random.randint(1, 10)]
            data[' Total Fwd Packets'] = [2]
            data['FIN Flag Count'] = [1]
            data[' SYN Flag Count'] = [1]
            
        elif attack_type == 'BruteForce':
            # SSH/FTP port, medium duration, many small packets
            data[' Destination Port'] = [22]
            data[' Total Fwd Packets'] = [np.random.randint(50, 200) * multiplier]
            data[' Fwd Packet Length Mean'] = [50]
            data[' PSH Flag Count'] = [1]
            
        return pd.DataFrame(data)
    
    @staticmethod
    def generate_syscall_sequence(attack_type='BENIGN', intensity='Medium', length=100):
        """
        Generate system call sequence for HIDS simulation
        
        Args:
            attack_type: 'BENIGN', 'Rootkit', 'Ransomware'
            intensity: 'Low', 'Medium', 'High'
            length: Sequence length
            
        Returns:
            List of syscall IDs
        """
        # Base multiplier
        multiplier = 1.0
        if intensity == 'Low': multiplier = 0.5
        elif intensity == 'High': multiplier = 2.0
        
        # Normal syscalls (common operations)
        normal_syscalls = [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15]
        
        if attack_type == 'Rootkit':
            # Rootkit: execve, setuid, write, open, close (privilege escalation pattern)
            malicious = [59, 105, 1, 2, 3]
            # Mix 60% malicious, 40% normal
            sequence = []
            for _ in range(length):
                if np.random.random() < 0.6 * multiplier:
                    sequence.append(np.random.choice(malicious))
                else:
                    sequence.append(np.random.choice(normal_syscalls))
            return sequence
            
        elif attack_type == 'Ransomware':
            # Ransomware: High frequency write/rename/open (file encryption pattern)
            malicious = [1, 82, 2]
            # Mix 70% malicious (very high I/O), 30% normal
            sequence = []
            for _ in range(int(length * (1 + multiplier))):
                if np.random.random() < 0.7:
                    sequence.append(np.random.choice(malicious))
                else:
                    sequence.append(np.random.choice(normal_syscalls))
            return sequence[:length]
            
        else:  # BENIGN
            # Normal distribution of common syscalls
            return list(np.random.choice(normal_syscalls, length))



def prompt_user_for_mock_data(dataset_name):
    """
    Prompt user if they want to generate mock data
    
    Args:
        dataset_name: Name of dataset (e.g., 'CIC-IDS2017', 'ADFA-LD')
        
    Returns:
        Boolean indicating user's choice
    """
    print(f"\n{'='*60}")
    print(f"[WARNING] {dataset_name} dataset not found!")
    print(f"{'='*60}")
    print(f"\nOptions:")
    print(f"1. Generate MOCK DATA for testing (quick, but not accurate)")
    print(f"2. Download real dataset (see scripts/download_instructions.py)")
    print(f"\nMock data is synthetic and will produce random results.")
    print(f"Use it ONLY for testing the code pipeline.")
    
    while True:
        choice = input(f"\nGenerate mock data? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            return True
        elif choice in ['n', 'no']:
            print(f"\n[ERROR] Cannot proceed without data.")
            print(f"Run: python scripts/download_instructions.py")
            return False
        else:
            print("Please enter 'y' or 'n'")


# Example usage
if __name__ == "__main__":
    print("="*60)
    print("Mock Data Generator for Hybrid IDS")
    print("="*60)
    
    generator = MockDataGenerator()
    
    # Generate CIC-IDS2017 mock
    print("\n1. Generating CIC-IDS2017 mock data...")
    cicids_file = generator.generate_cicids2017_mock(num_samples=1000)
    
    # Generate ADFA-LD mock
    print("\n2. Generating ADFA-LD mock data...")
    training_dir, attack_dir = generator.generate_adfa_ld_mock(
        num_normal=100,
        num_attack=50
    )
    
    print("\n" + "="*60)
    print("[SUCCESS] Mock data generation complete!")
    print("="*60)
    print("\n[WARNING] This is MOCK DATA for testing only!")
    print("Models trained on this data will have random accuracy.")
    print("\nFor real results, download actual datasets:")
    print("  python scripts/download_instructions.py")

    
    @staticmethod
    def get_cicids_feature_names():
        """Get list of CIC-IDS2017 feature names"""
        return [
            ' Destination Port', ' Flow Duration', ' Total Fwd Packets',
            ' Total Backward Packets', 'Total Length of Fwd Packets',
            ' Total Length of Bwd Packets', ' Fwd Packet Length Max',
            ' Fwd Packet Length Min', ' Fwd Packet Length Mean',
            ' Fwd Packet Length Std', 'Bwd Packet Length Max',
            ' Bwd Packet Length Min', ' Bwd Packet Length Mean',
            ' Bwd Packet Length Std', 'Flow Bytes/s', ' Flow Packets/s',
            ' Flow IAT Mean', ' Flow IAT Std', ' Flow IAT Max', ' Flow IAT Min',
            'Fwd IAT Total', ' Fwd IAT Mean', ' Fwd IAT Std', ' Fwd IAT Max',
            ' Fwd IAT Min', 'Bwd IAT Total', ' Bwd IAT Mean', ' Bwd IAT Std',
            ' Bwd IAT Max', ' Bwd IAT Min', 'Fwd PSH Flags', ' Bwd PSH Flags',
            ' Fwd URG Flags', ' Bwd URG Flags', ' Fwd Header Length',
            ' Bwd Header Length', 'Fwd Packets/s', ' Bwd Packets/s',
            ' Min Packet Length', ' Max Packet Length', ' Packet Length Mean',
            ' Packet Length Std', ' Packet Length Variance', 'FIN Flag Count',
            ' SYN Flag Count', ' RST Flag Count', ' PSH Flag Count',
            ' ACK Flag Count', ' URG Flag Count', ' CWE Flag Count',
            ' ECE Flag Count', ' Down/Up Ratio', ' Average Packet Size',
            ' Avg Fwd Segment Size', ' Avg Bwd Segment Size',
            'Fwd Header Length.1', ' Fwd Avg Bytes/Bulk', ' Fwd Avg Packets/Bulk',
            ' Fwd Avg Bulk Rate', ' Bwd Avg Bytes/Bulk', ' Bwd Avg Packets/Bulk',
            ' Bwd Avg Bulk Rate', 'Subflow Fwd Packets', ' Subflow Fwd Bytes',
            ' Subflow Bwd Packets', ' Subflow Bwd Bytes',
            ' Init_Win_bytes_forward', ' Init_Win_bytes_backward',
            ' act_data_pkt_fwd', ' min_seg_size_forward', 'Active Mean',
            ' Active Std', ' Active Max', ' Active Min', 'Idle Mean',
            ' Idle Std', ' Idle Max', ' Idle Min'
        ]

    @staticmethod
    def generate_single_sample(attack_type='BENIGN', intensity='Medium'):
        """
        Generate a single feature sample for real-time simulation
        
        Args:
            attack_type: 'BENIGN', 'DDoS', 'PortScan', 'BruteForce'
            intensity: 'Low', 'Medium', 'High'
            
        Returns:
            DataFrame with 1 row and 78 features
        """
        feature_names = MockDataGenerator.get_cicids_feature_names()
        data = {}
        
        # Base multipliers based on intensity
        multiplier = 1.0
        if intensity == 'Low': multiplier = 0.5
        elif intensity == 'High': multiplier = 2.0
        
        # Generate base random data (Normal-ish)
        for feature in feature_names:
            if 'Port' in feature:
                data[feature] = [np.random.choice([80, 443, 22, 53])]
            elif 'Flag' in feature or 'Count' in feature:
                data[feature] = [0]
            else:
                data[feature] = [np.abs(np.random.randn() * 100)]
        
        # Inject Attack Patterns
        if attack_type == 'DDoS':
            # High packet count, small duration, high bytes/sec
            data[' Total Fwd Packets'] = [np.random.randint(1000, 5000) * multiplier]
            data[' Flow Duration'] = [np.random.randint(100, 1000)]
            data['Flow Bytes/s'] = [np.random.randint(100000, 1000000) * multiplier]
            data[' Fwd Packet Length Max'] = [1000 * multiplier]
            
        elif attack_type == 'PortScan':
            # Many ports (handled by logic outside, but features show short flows)
            data[' Flow Duration'] = [np.random.randint(1, 10)]
            data[' Total Fwd Packets'] = [2]
            data['FIN Flag Count'] = [1]
            data[' SYN Flag Count'] = [1]
            
        elif attack_type == 'BruteForce':
            # SSH/FTP port, medium duration, many small packets
            data[' Destination Port'] = [22]
            data[' Total Fwd Packets'] = [np.random.randint(50, 200) * multiplier]
            data[' Fwd Packet Length Mean'] = [50]
            data[' PSH Flag Count'] = [1]
            
        return pd.DataFrame(data)
    
    @staticmethod
    def generate_syscall_sequence(attack_type='BENIGN', intensity='Medium', length=100):
        """
        Generate system call sequence for HIDS simulation
        
        Args:
            attack_type: 'BENIGN', 'Rootkit', 'Ransomware'
            intensity: 'Low', 'Medium', 'High'
            length: Sequence length
            
        Returns:
            List of syscall IDs
        """
        # Base multiplier
        multiplier = 1.0
        if intensity == 'Low': multiplier = 0.5
        elif intensity == 'High': multiplier = 2.0
        
        # Normal syscalls (common operations)
        normal_syscalls = [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15]
        
        if attack_type == 'Rootkit':
            # Rootkit: execve, setuid, write, open, close (privilege escalation pattern)
            malicious = [59, 105, 1, 2, 3]
            # Mix 60% malicious, 40% normal
            sequence = []
            for _ in range(length):
                if np.random.random() < 0.6 * multiplier:
                    sequence.append(np.random.choice(malicious))
                else:
                    sequence.append(np.random.choice(normal_syscalls))
            return sequence
            
        elif attack_type == 'Ransomware':
            # Ransomware: High frequency write/rename/open (file encryption pattern)
            malicious = [1, 82, 2]
            # Mix 70% malicious (very high I/O), 30% normal
            sequence = []
            for _ in range(int(length * (1 + multiplier))):
                if np.random.random() < 0.7:
                    sequence.append(np.random.choice(malicious))
                else:
                    sequence.append(np.random.choice(normal_syscalls))
            return sequence[:length]
            
        else:  # BENIGN
            # Normal distribution of common syscalls
            return list(np.random.choice(normal_syscalls, length))



def prompt_user_for_mock_data(dataset_name):
    """
    Prompt user if they want to generate mock data
    
    Args:
        dataset_name: Name of dataset (e.g., 'CIC-IDS2017', 'ADFA-LD')
        
    Returns:
        Boolean indicating user's choice
    """
    print(f"\n{'='*60}")
    print(f"[WARNING] {dataset_name} dataset not found!")
    print(f"{'='*60}")
    print(f"\nOptions:")
    print(f"1. Generate MOCK DATA for testing (quick, but not accurate)")
    print(f"2. Download real dataset (see scripts/download_instructions.py)")
    print(f"\nMock data is synthetic and will produce random results.")
    print(f"Use it ONLY for testing the code pipeline.")
    
    while True:
        choice = input(f"\nGenerate mock data? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            return True
        elif choice in ['n', 'no']:
            print(f"\n[ERROR] Cannot proceed without data.")
            print(f"Run: python scripts/download_instructions.py")
            return False
        else:
            print("Please enter 'y' or 'n'")


# Example usage
if __name__ == "__main__":
    print("="*60)
    print("Mock Data Generator for Hybrid IDS")
    print("="*60)
    
    generator = MockDataGenerator()
    
    # Generate CIC-IDS2017 mock
    print("\n1. Generating CIC-IDS2017 mock data...")
    cicids_file = generator.generate_cicids2017_mock(num_samples=1000)
    
    # Generate ADFA-LD mock
    print("\n2. Generating ADFA-LD mock data...")
    training_dir, attack_dir = generator.generate_adfa_ld_mock(
        num_normal=100,
        num_attack=50
    )
    
    print("\n" + "="*60)
    print("[SUCCESS] Mock data generation complete!")
    print("="*60)
    print("\n[WARNING] This is MOCK DATA for testing only!")
    print("Models trained on this data will have random accuracy.")
    print("\nFor real results, download actual datasets:")
    print("  python scripts/download_instructions.py")

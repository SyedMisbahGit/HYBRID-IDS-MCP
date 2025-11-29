"""
HIDS Data Loader for ADFA-LD Dataset

This module handles loading and preprocessing of the ADFA-LD (Linux Dataset)
for training LSTM-based sequence analysis models.
"""

import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ADFALDLoader:
    """
    Load and preprocess ADFA-LD dataset
    
    The dataset contains system call traces from Linux hosts.
    - Training data: Normal behavior traces
    - Attack data: Various attack scenarios
    """
    
    def __init__(self, data_dir=None):
        """
        Initialize loader
        
        Args:
            data_dir: Directory containing ADFA-LD dataset
                     If None, automatically checks data/raw/ then data/mock/
        """
        # Auto-detect data directory
        if data_dir is None:
            if os.path.exists('data/raw/adfa-ld/Training_Data_Master'):
                data_dir = 'data/raw/adfa-ld'
                logger.info("Using real data from data/raw/adfa-ld")
            elif os.path.exists('data/mock/adfa-ld/Training_Data_Master'):
                data_dir = 'data/mock/adfa-ld'
                logger.warning("⚠️  Using MOCK data from data/mock/adfa-ld")
            else:
                data_dir = 'data/raw/adfa-ld'  # Default fallback
        
        self.data_dir = data_dir
        self.syscall_encoder = LabelEncoder()
        self.max_sequence_length = 100
        
    def load_traces(self, trace_type='training', use_mock_if_missing=True):
        """
        Load system call traces
        
        Args:
            trace_type: 'training' (normal) or 'attack'
            use_mock_if_missing: If True, offer to generate mock data if real data not found
            
        Returns:
            List of traces (each trace is a list of system calls)
        """
        if trace_type == 'training':
            trace_dir = os.path.join(self.data_dir, 'Training_Data_Master')
        else:
            trace_dir = os.path.join(self.data_dir, 'Attack_Data_Master')
        
        logger.info(f"Loading {trace_type} traces from {trace_dir}")
        
        if not os.path.exists(trace_dir):
            if use_mock_if_missing:
                logger.warning(f"Directory not found: {trace_dir}")
                logger.warning("Attempting to use mock data...")
                
                # Try to import mock generator
                try:
                    import sys
                    sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
                    from utils.mock_generator import MockDataGenerator, prompt_user_for_mock_data
                    
                    # Ask user (only once for ADFA-LD)
                    if not hasattr(self, '_mock_generated'):
                        if prompt_user_for_mock_data('ADFA-LD'):
                            generator = MockDataGenerator()
                            generator.generate_adfa_ld_mock(output_dir=self.data_dir)
                            self._mock_generated = True
                            logger.warning("⚠️  USING MOCK DATA - Results will be random!")
                        else:
                            raise FileNotFoundError(
                                f"Directory not found: {trace_dir}\n"
                                f"Run: python scripts/download_instructions.py"
                            )
                except ImportError:
                    raise FileNotFoundError(
                        f"Directory not found: {trace_dir}\n"
                        f"Run: python scripts/download_instructions.py"
                    )
            else:
                raise FileNotFoundError(f"Directory not found: {trace_dir}")
        
        traces = []
        trace_files = [f for f in os.listdir(trace_dir) if f.startswith('U')]
        
        logger.info(f"Found {len(trace_files)} trace files")
        
        for trace_file in trace_files:
            file_path = os.path.join(trace_dir, trace_file)
            
            try:
                # Read system calls from file
                with open(file_path, 'r') as f:
                    syscalls = f.read().strip().split()
                    # Convert to integers
                    syscalls = [int(sc) for sc in syscalls if sc.isdigit()]
                    traces.append(syscalls)
            except Exception as e:
                logger.warning(f"Error reading {trace_file}: {e}")
                continue
        
        logger.info(f"Loaded {len(traces)} traces")
        return traces
    
    def create_sequences(self, traces, window_size=100, stride=50):
        """
        Create fixed-length sequences from variable-length traces
        
        Args:
            traces: List of system call traces
            window_size: Length of each sequence
            stride: Step size for sliding window
            
        Returns:
            Array of sequences
        """
        logger.info(f"Creating sequences (window={window_size}, stride={stride})...")
        
        sequences = []
        
        for trace in traces:
            # Slide window over trace
            for i in range(0, len(trace) - window_size + 1, stride):
                sequence = trace[i:i + window_size]
                sequences.append(sequence)
        
        logger.info(f"Created {len(sequences)} sequences")
        return np.array(sequences)
    
    def encode_syscalls(self, sequences):
        """
        Encode system calls to sequential integers
        
        Args:
            sequences: Array of sequences
            
        Returns:
            Encoded sequences
        """
        logger.info("Encoding system calls...")
        
        # Flatten all sequences to fit encoder
        all_syscalls = sequences.flatten()
        
        # Fit encoder
        self.syscall_encoder.fit(all_syscalls)
        
        logger.info(f"Unique system calls: {len(self.syscall_encoder.classes_)}")
        
        # Encode sequences
        encoded_sequences = np.array([
            self.syscall_encoder.transform(seq) for seq in sequences
        ])
        
        return encoded_sequences
    
    def prepare_data(self, window_size=100, stride=50, test_size=0.2, random_state=42):
        """
        Prepare data for LSTM training
        
        Args:
            window_size: Sequence length
            stride: Sliding window stride
            test_size: Fraction for testing
            random_state: Random seed
            
        Returns:
            X_train, X_test, y_train, y_test
        """
        logger.info("Preparing ADFA-LD data...")
        
        # Load normal traces
        normal_traces = self.load_traces('training')
        
        # Load attack traces
        attack_traces = self.load_traces('attack')
        
        # Create sequences
        normal_sequences = self.create_sequences(normal_traces, window_size, stride)
        attack_sequences = self.create_sequences(attack_traces, window_size, stride)
        
        # Encode system calls
        all_sequences = np.vstack([normal_sequences, attack_sequences])
        encoded_sequences = self.encode_syscalls(all_sequences)
        
        # Split back into normal and attack
        num_normal = len(normal_sequences)
        normal_encoded = encoded_sequences[:num_normal]
        attack_encoded = encoded_sequences[num_normal:]
        
        # Create labels (0 = normal, 1 = attack)
        normal_labels = np.zeros(len(normal_encoded))
        attack_labels = np.ones(len(attack_encoded))
        
        # Combine
        X = np.vstack([normal_encoded, attack_encoded])
        y = np.concatenate([normal_labels, attack_labels])
        
        logger.info(f"Total sequences: {len(X)} (Normal: {len(normal_encoded)}, Attack: {len(attack_encoded)})")
        
        # Split into train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        logger.info(f"Training: {len(X_train)} sequences")
        logger.info(f"Testing: {len(X_test)} sequences")
        
        return X_train, X_test, y_train, y_test
    
    def get_vocab_size(self):
        """Get vocabulary size (number of unique system calls)"""
        return len(self.syscall_encoder.classes_)
    
    def get_encoder(self):
        """Get fitted syscall encoder"""
        return self.syscall_encoder


# Example usage
if __name__ == "__main__":
    # Initialize loader
    loader = ADFALDLoader(data_dir='../../data/raw/adfa-ld')
    
    try:
        # Prepare data
        X_train, X_test, y_train, y_test = loader.prepare_data(
            window_size=100,
            stride=50
        )
        
        print(f"\n✅ Data loading successful!")
        print(f"Train shape: {X_train.shape}")
        print(f"Test shape: {X_test.shape}")
        print(f"Vocabulary size: {loader.get_vocab_size()}")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("Please download ADFA-LD dataset and extract to data/raw/adfa-ld/")

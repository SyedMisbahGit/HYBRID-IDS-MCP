"""
NIDS Data Loader for CIC-IDS2017 Dataset

This module handles loading and preprocessing of the CIC-IDS2017 dataset
for training SIDS (supervised) and A-IDS (anomaly detection) models.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CICIDS2017Loader:
    """
    Load and preprocess CIC-IDS2017 dataset
    
    The dataset contains network flow features and attack labels.
    Features: 78 CIC flow features
    Labels: Benign, DoS, DDoS, PortScan, BruteForce, WebAttack, etc.
    """
    
    def __init__(self, data_dir=None):
        """
        Initialize loader
        
        Args:
            data_dir: Directory containing CIC-IDS2017 CSV files
                     If None, automatically checks data/raw/ then data/mock/
        """
        # Auto-detect data directory
        if data_dir is None:
            if os.path.exists('data/raw/cicids2017') and os.listdir('data/raw/cicids2017'):
                data_dir = 'data/raw/cicids2017'
                logger.info("Using real data from data/raw/cicids2017")
            elif os.path.exists('data/mock/cicids2017') and os.listdir('data/mock/cicids2017'):
                data_dir = 'data/mock/cicids2017'
                logger.warning("⚠️  Using MOCK data from data/mock/cicids2017")
            else:
                data_dir = 'data/raw/cicids2017'  # Default fallback
        
        self.data_dir = data_dir
        self.feature_columns = None
        self.label_encoder = LabelEncoder()
        self.scaler = StandardScaler()
        
    def load_data(self, sample_size=None, use_mock_if_missing=True):
        """
        Load CIC-IDS2017 dataset from CSV files
        
        Args:
            sample_size: If specified, load only this many samples (for testing)
            use_mock_if_missing: If True, offer to generate mock data if real data not found
            
        Returns:
            DataFrame with features and labels
        """
        logger.info(f"Loading CIC-IDS2017 dataset from {self.data_dir}")
        
        # Check if directory exists
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)
        
        # CIC-IDS2017 typically has multiple CSV files (one per day)
        csv_files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
        
        if not csv_files:
            if use_mock_if_missing:
                logger.warning(f"No CSV files found in {self.data_dir}")
                logger.warning("Attempting to use mock data...")
                
                # Try to import mock generator
                try:
                    import sys
                    sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
                    from utils.mock_generator import MockDataGenerator, prompt_user_for_mock_data
                    
                    # Ask user
                    if prompt_user_for_mock_data('CIC-IDS2017'):
                        generator = MockDataGenerator()
                        mock_file = generator.generate_cicids2017_mock(
                            output_dir=self.data_dir,
                            num_samples=sample_size or 1000
                        )
                        csv_files = [os.path.basename(mock_file)]
                        logger.warning("⚠️  USING MOCK DATA - Results will be random!")
                    else:
                        raise FileNotFoundError(
                            f"No CSV files found in {self.data_dir}\n"
                            f"Run: python scripts/download_instructions.py"
                        )
                except ImportError:
                    raise FileNotFoundError(
                        f"No CSV files found in {self.data_dir}\n"
                        f"Run: python scripts/download_instructions.py"
                    )
            else:
                raise FileNotFoundError(f"No CSV files found in {self.data_dir}")
        
        logger.info(f"Found {len(csv_files)} CSV files")
        
        # Load all CSV files
        dfs = []
        for csv_file in csv_files:
            file_path = os.path.join(self.data_dir, csv_file)
            logger.info(f"Loading {csv_file}...")
            
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except:
                df = pd.read_csv(file_path, encoding='latin-1')
            
            dfs.append(df)
        
        # Concatenate all dataframes
        data = pd.concat(dfs, ignore_index=True)
        logger.info(f"Total samples loaded: {len(data)}")
        
        # Sample if requested
        if sample_size and sample_size < len(data):
            data = data.sample(n=sample_size, random_state=42)
            logger.info(f"Sampled {sample_size} rows")
        
        return data
    
    def preprocess(self, data, target_column=' Label'):
        """
        Preprocess the dataset
        
        Args:
            data: Raw dataframe
            target_column: Name of the label column
            
        Returns:
            X (features), y (labels)
        """
        logger.info("Preprocessing data...")
        
        # Handle column name variations
        if target_column not in data.columns:
            # Try without leading space
            target_column = 'Label'
        
        # Separate features and labels
        y = data[target_column].copy()
        X = data.drop(columns=[target_column])
        
        # Remove non-numeric columns (if any)
        X = X.select_dtypes(include=[np.number])
        
        # Handle missing values
        X = X.fillna(0)
        
        # Handle infinite values
        X = X.replace([np.inf, -np.inf], 0)
        
        # Store feature columns
        self.feature_columns = X.columns.tolist()
        logger.info(f"Number of features: {len(self.feature_columns)}")
        
        # Clean labels (remove leading/trailing spaces)
        y = y.str.strip()
        
        logger.info(f"Label distribution:\n{y.value_counts()}")
        
        return X, y
    
    def prepare_for_sids(self, X, y, test_size=0.2, random_state=42):
        """
        Prepare data for SIDS (supervised classification)
        
        Args:
            X: Features
            y: Labels
            test_size: Fraction of data for testing
            random_state: Random seed
            
        Returns:
            X_train, X_test, y_train, y_test, scaler, label_encoder
        """
        logger.info("Preparing data for SIDS (supervised learning)...")
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        logger.info(f"Label classes: {self.label_encoder.classes_}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=test_size, random_state=random_state, stratify=y_encoded
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        logger.info(f"Training samples: {len(X_train)}")
        logger.info(f"Testing samples: {len(X_test)}")
        
        return X_train_scaled, X_test_scaled, y_train, y_test
    
    def prepare_for_aids(self, X, y, test_size=0.2, random_state=42):
        """
        Prepare data for A-IDS (anomaly detection)
        Only use BENIGN traffic for training
        
        Args:
            X: Features
            y: Labels
            test_size: Fraction of data for testing
            random_state: Random seed
            
        Returns:
            X_train_benign, X_test, y_test_binary, scaler
        """
        logger.info("Preparing data for A-IDS (anomaly detection)...")
        
        # Create binary labels (0 = Benign, 1 = Attack)
        y_binary = (y != 'BENIGN').astype(int)
        
        # Split data
        X_train, X_test, y_train_binary, y_test_binary = train_test_split(
            X, y_binary, test_size=test_size, random_state=random_state, stratify=y_binary
        )
        
        # For training, use ONLY benign samples
        X_train_benign = X_train[y_train_binary == 0]
        logger.info(f"Benign training samples: {len(X_train_benign)}")
        
        # Scale features (fit only on benign data)
        X_train_benign_scaled = self.scaler.fit_transform(X_train_benign)
        X_test_scaled = self.scaler.transform(X_test)
        
        logger.info(f"Testing samples: {len(X_test)} (Benign: {sum(y_test_binary==0)}, Attack: {sum(y_test_binary==1)})")
        
        return X_train_benign_scaled, X_test_scaled, y_test_binary
    
    def get_feature_names(self):
        """Get list of feature names"""
        return self.feature_columns
    
    def get_label_encoder(self):
        """Get fitted label encoder"""
        return self.label_encoder
    
    def get_scaler(self):
        """Get fitted scaler"""
        return self.scaler


# Example usage
if __name__ == "__main__":
    # Initialize loader
    loader = CICIDS2017Loader(data_dir='../../data/raw/cicids2017')
    
    try:
        # Load data (use sample for testing)
        data = loader.load_data(sample_size=10000)
        
        # Preprocess
        X, y = loader.preprocess(data)
        
        # Prepare for SIDS
        print("\n=== SIDS Preparation ===")
        X_train, X_test, y_train, y_test = loader.prepare_for_sids(X, y)
        print(f"SIDS - Train shape: {X_train.shape}, Test shape: {X_test.shape}")
        
        # Prepare for A-IDS
        print("\n=== A-IDS Preparation ===")
        X_train_benign, X_test, y_test_binary = loader.prepare_for_aids(X, y)
        print(f"A-IDS - Benign train shape: {X_train_benign.shape}, Test shape: {X_test.shape}")
        
        print("\n✅ Data loading successful!")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("Please download CIC-IDS2017 dataset and place CSV files in data/raw/cicids2017/")

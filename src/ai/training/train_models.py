#!/usr/bin/env python3
"""
ML Model Training for Hybrid IDS
Trains Random Forest and Isolation Forest models for anomaly detection
"""

import argparse
import logging
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    Trains ML models for network intrusion detection
    """
    
    def __init__(self, output_dir: str = 'models'):
        """
        Initialize model trainer
        
        Args:
            output_dir: Directory to save trained models
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.scaler = None
        self.rf_model = None
        self.if_model = None
        
        # 78 feature names (matching feature extractor)
        self.feature_names = [
            'duration', 'total_fwd_packets', 'total_bwd_packets',
            'total_fwd_bytes', 'total_bwd_bytes',
            'fwd_pkt_len_max', 'fwd_pkt_len_min', 'fwd_pkt_len_mean', 'fwd_pkt_len_std',
            'bwd_pkt_len_max', 'bwd_pkt_len_min', 'bwd_pkt_len_mean', 'bwd_pkt_len_std',
            'flow_bytes_per_sec', 'flow_packets_per_sec',
            'flow_iat_mean', 'flow_iat_std', 'flow_iat_max', 'flow_iat_min',
            'fwd_iat_total', 'fwd_iat_mean', 'fwd_iat_std', 'fwd_iat_max', 'fwd_iat_min',
            'bwd_iat_total', 'bwd_iat_mean', 'bwd_iat_std', 'bwd_iat_max', 'bwd_iat_min',
            'fwd_psh_flags', 'bwd_psh_flags', 'fwd_urg_flags', 'bwd_urg_flags',
            'fwd_header_len', 'bwd_header_len', 'fwd_packets_per_sec', 'bwd_packets_per_sec',
            'pkt_len_min', 'pkt_len_max', 'pkt_len_mean', 'pkt_len_std', 'pkt_len_variance',
            'fin_flag_count', 'syn_flag_count', 'rst_flag_count', 'psh_flag_count',
            'ack_flag_count', 'urg_flag_count', 'cwe_flag_count', 'ece_flag_count',
            'down_up_ratio', 'avg_packet_size', 'avg_fwd_segment_size', 'avg_bwd_segment_size',
            'fwd_bulk_rate_avg', 'fwd_bulk_size_avg', 'fwd_bulk_packets_avg',
            'bwd_bulk_rate_avg', 'bwd_bulk_size_avg', 'bwd_bulk_packets_avg',
            'subflow_fwd_packets', 'subflow_fwd_bytes', 'subflow_bwd_packets', 'subflow_bwd_bytes',
            'init_fwd_win_bytes', 'init_bwd_win_bytes', 'act_data_pkt_fwd', 'min_seg_size_fwd',
            'active_mean', 'active_std', 'active_max', 'active_min',
            'idle_mean', 'idle_std', 'idle_max', 'idle_min'
        ]
    
    def generate_synthetic_data(self, n_samples: int = 10000):
        """
        Generate synthetic network traffic data for training
        
        Args:
            n_samples: Number of samples to generate
            
        Returns:
            X: Features, y: Labels
        """
        logger.info(f"Generating {n_samples} synthetic samples...")
        
        np.random.seed(42)
        
        # Generate normal traffic (70%)
        n_normal = int(n_samples * 0.7)
        normal_data = []
        
        for _ in range(n_normal):
            sample = {
                'duration': np.random.exponential(5),
                'total_fwd_packets': np.random.poisson(10),
                'total_bwd_packets': np.random.poisson(8),
                'total_fwd_bytes': np.random.normal(5000, 1000),
                'total_bwd_bytes': np.random.normal(4000, 800),
                'fwd_pkt_len_mean': np.random.normal(500, 100),
                'bwd_pkt_len_mean': np.random.normal(400, 80),
                'flow_bytes_per_sec': np.random.normal(1000, 200),
                'flow_packets_per_sec': np.random.normal(2, 0.5),
                'syn_flag_count': np.random.poisson(1),
                'ack_flag_count': np.random.poisson(10),
                'avg_packet_size': np.random.normal(450, 100),
            }
            # Fill remaining features with normal values
            for feat in self.feature_names:
                if feat not in sample:
                    sample[feat] = np.random.normal(0, 1)
            normal_data.append(sample)
        
        # Generate attack traffic (30%)
        n_attack = n_samples - n_normal
        attack_data = []
        
        for _ in range(n_attack):
            attack_type = np.random.choice(['dos', 'probe', 'exploit'])
            
            if attack_type == 'dos':
                # DoS: High packet rate, small packets
                sample = {
                    'duration': np.random.exponential(1),
                    'total_fwd_packets': np.random.poisson(1000),
                    'total_bwd_packets': np.random.poisson(10),
                    'total_fwd_bytes': np.random.normal(50000, 10000),
                    'total_bwd_bytes': np.random.normal(500, 100),
                    'fwd_pkt_len_mean': np.random.normal(50, 10),
                    'bwd_pkt_len_mean': np.random.normal(50, 10),
                    'flow_bytes_per_sec': np.random.normal(50000, 10000),
                    'flow_packets_per_sec': np.random.normal(1000, 200),
                    'syn_flag_count': np.random.poisson(500),
                    'ack_flag_count': np.random.poisson(10),
                    'avg_packet_size': np.random.normal(50, 10),
                }
            elif attack_type == 'probe':
                # Port scan: Many connections, few packets each
                sample = {
                    'duration': np.random.exponential(0.1),
                    'total_fwd_packets': np.random.poisson(2),
                    'total_bwd_packets': np.random.poisson(1),
                    'total_fwd_bytes': np.random.normal(100, 20),
                    'total_bwd_bytes': np.random.normal(50, 10),
                    'fwd_pkt_len_mean': np.random.normal(50, 10),
                    'bwd_pkt_len_mean': np.random.normal(50, 10),
                    'flow_bytes_per_sec': np.random.normal(1000, 200),
                    'flow_packets_per_sec': np.random.normal(20, 5),
                    'syn_flag_count': np.random.poisson(1),
                    'ack_flag_count': np.random.poisson(0),
                    'avg_packet_size': np.random.normal(50, 10),
                }
            else:  # exploit
                # Exploit: Normal-ish but with anomalies
                sample = {
                    'duration': np.random.exponential(10),
                    'total_fwd_packets': np.random.poisson(50),
                    'total_bwd_packets': np.random.poisson(40),
                    'total_fwd_bytes': np.random.normal(25000, 5000),
                    'total_bwd_bytes': np.random.normal(20000, 4000),
                    'fwd_pkt_len_mean': np.random.normal(500, 200),
                    'bwd_pkt_len_mean': np.random.normal(500, 200),
                    'flow_bytes_per_sec': np.random.normal(2500, 500),
                    'flow_packets_per_sec': np.random.normal(9, 2),
                    'syn_flag_count': np.random.poisson(2),
                    'ack_flag_count': np.random.poisson(50),
                    'avg_packet_size': np.random.normal(500, 150),
                }
            
            # Fill remaining features
            for feat in self.feature_names:
                if feat not in sample:
                    sample[feat] = np.random.normal(0, 2)  # More variance for attacks
            attack_data.append(sample)
        
        # Combine data
        all_data = normal_data + attack_data
        labels = [0] * n_normal + [1] * n_attack  # 0=normal, 1=attack
        
        # Convert to DataFrame
        df = pd.DataFrame(all_data)
        df = df[self.feature_names]  # Ensure correct order
        
        logger.info(f"Generated {n_normal} normal and {n_attack} attack samples")
        
        return df.values, np.array(labels)
    
    def train_random_forest(self, X_train, y_train, X_test, y_test):
        """
        Train Random Forest classifier
        
        Args:
            X_train, y_train: Training data
            X_test, y_test: Test data
        """
        logger.info("Training Random Forest classifier...")
        
        self.rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=20,
            min_samples_split=10,
            min_samples_leaf=4,
            random_state=42,
            n_jobs=-1,
            verbose=1
        )
        
        self.rf_model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.rf_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        logger.info(f"Random Forest Accuracy: {accuracy:.4f}")
        logger.info("\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=['Normal', 'Attack']))
        
        # Save model
        model_path = self.output_dir / 'random_forest_model.pkl'
        joblib.dump(self.rf_model, model_path)
        logger.info(f"Saved Random Forest model to {model_path}")
        
        return accuracy
    
    def train_isolation_forest(self, X_train):
        """
        Train Isolation Forest for anomaly detection
        
        Args:
            X_train: Training data (normal traffic only)
        """
        logger.info("Training Isolation Forest...")
        
        self.if_model = IsolationForest(
            n_estimators=100,
            max_samples='auto',
            contamination=0.1,  # Expect 10% anomalies
            random_state=42,
            n_jobs=-1,
            verbose=1
        )
        
        self.if_model.fit(X_train)
        
        # Save model
        model_path = self.output_dir / 'isolation_forest_model.pkl'
        joblib.dump(self.if_model, model_path)
        logger.info(f"Saved Isolation Forest model to {model_path}")
    
    def train_scaler(self, X_train):
        """
        Train StandardScaler for feature normalization
        
        Args:
            X_train: Training data
        """
        logger.info("Training StandardScaler...")
        
        self.scaler = StandardScaler()
        self.scaler.fit(X_train)
        
        # Save scaler
        scaler_path = self.output_dir / 'scaler.pkl'
        joblib.dump(self.scaler, scaler_path)
        logger.info(f"Saved scaler to {scaler_path}")
    
    def train_all(self, dataset_path: str = None, use_synthetic: bool = True):
        """
        Train all models
        
        Args:
            dataset_path: Path to dataset CSV (if available)
            use_synthetic: Use synthetic data if dataset not available
        """
        logger.info("="*70)
        logger.info("  ML Model Training for Hybrid IDS")
        logger.info("="*70)
        logger.info("")
        
        # Load or generate data
        if dataset_path and Path(dataset_path).exists():
            logger.info(f"Loading dataset from {dataset_path}")
            df = pd.read_csv(dataset_path)
            X = df[self.feature_names].values
            y = df['label'].values
        elif use_synthetic:
            logger.info("Using synthetic data (no dataset provided)")
            X, y = self.generate_synthetic_data(n_samples=10000)
        else:
            logger.error("No dataset provided and synthetic data disabled")
            return False
        
        logger.info(f"Dataset shape: {X.shape}")
        logger.info(f"Normal samples: {np.sum(y == 0)}")
        logger.info(f"Attack samples: {np.sum(y == 1)}")
        logger.info("")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        logger.info(f"Training set: {X_train.shape[0]} samples")
        logger.info(f"Test set: {X_test.shape[0]} samples")
        logger.info("")
        
        # Train scaler
        self.train_scaler(X_train)
        
        # Scale data
        X_train_scaled = self.scaler.transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest
        rf_accuracy = self.train_random_forest(X_train_scaled, y_train, X_test_scaled, y_test)
        logger.info("")
        
        # Train Isolation Forest (on normal traffic only)
        X_train_normal = X_train_scaled[y_train == 0]
        self.train_isolation_forest(X_train_normal)
        logger.info("")
        
        # Save metadata
        metadata = {
            'training_date': datetime.now().isoformat(),
            'n_features': len(self.feature_names),
            'feature_names': self.feature_names,
            'n_train_samples': X_train.shape[0],
            'n_test_samples': X_test.shape[0],
            'rf_accuracy': float(rf_accuracy),
            'dataset_type': 'synthetic' if use_synthetic else 'real'
        }
        
        import json
        metadata_path = self.output_dir / 'model_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved metadata to {metadata_path}")
        
        logger.info("")
        logger.info("="*70)
        logger.info("  Training Complete!")
        logger.info("="*70)
        logger.info(f"Models saved to: {self.output_dir}")
        logger.info("  - random_forest_model.pkl")
        logger.info("  - isolation_forest_model.pkl")
        logger.info("  - scaler.pkl")
        logger.info("  - model_metadata.json")
        logger.info("")
        
        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Train ML models for Hybrid IDS')
    parser.add_argument('--dataset', type=str, help='Path to dataset CSV file')
    parser.add_argument('--output-dir', type=str, default='models', help='Output directory for models')
    parser.add_argument('--no-synthetic', action='store_true', help='Disable synthetic data generation')
    parser.add_argument('--samples', type=int, default=10000, help='Number of synthetic samples')
    
    args = parser.parse_args()
    
    trainer = ModelTrainer(output_dir=args.output_dir)
    
    try:
        success = trainer.train_all(
            dataset_path=args.dataset,
            use_synthetic=not args.no_synthetic
        )
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

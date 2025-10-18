#!/usr/bin/env python3
"""
Anomaly Detector - Real-time ML-based intrusion detection
Receives flow features from NIDS and performs anomaly detection using ML models
"""

import json
import logging
import time
import sys
from typing import Dict, List, Tuple
from pathlib import Path

import numpy as np
import joblib

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Real-time anomaly detection using ensemble of ML models
    """

    def __init__(self, config_path: str = None):
        """
        Initialize anomaly detector

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.models = {}
        self.scaler = None
        self.feature_names = self._get_feature_names()
        self.stats = {
            'total_flows': 0,
            'anomalies_detected': 0,
            'benign_flows': 0,
            'avg_inference_time_ms': 0.0
        }

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration"""
        default_config = {
            'models': {
                'random_forest': {
                    'path': 'models/random_forest_model.pkl',
                    'weight': 0.5,
                    'enabled': True
                },
                'isolation_forest': {
                    'path': 'models/isolation_forest_model.pkl',
                    'weight': 0.5,
                    'enabled': True
                }
            },
            'scaler_path': 'models/scaler.pkl',
            'threshold': 0.7,
            'feature_count': 78
        }

        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                import yaml
                user_config = yaml.safe_load(f)
                default_config.update(user_config)

        return default_config

    def _get_feature_names(self) -> List[str]:
        """Get list of 78 feature names (matching C++ extractor)"""
        return [
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

    def load_models(self) -> bool:
        """
        Load ML models and scaler

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load scaler
            scaler_path = self.config.get('scaler_path')
            if scaler_path and Path(scaler_path).exists():
                self.scaler = joblib.load(scaler_path)
                logger.info(f"Loaded scaler from {scaler_path}")
            else:
                logger.warning("No scaler found, will use raw features")

            # Load models
            for model_name, model_config in self.config['models'].items():
                if not model_config.get('enabled', False):
                    continue

                model_path = model_config.get('path')
                if model_path and Path(model_path).exists():
                    self.models[model_name] = {
                        'model': joblib.load(model_path),
                        'weight': model_config.get('weight', 1.0)
                    }
                    logger.info(f"Loaded model: {model_name} from {model_path}")
                else:
                    logger.warning(f"Model file not found: {model_path}")

            if not self.models:
                logger.warning("No models loaded! Creating dummy models for testing...")
                self._create_dummy_models()

            return len(self.models) > 0

        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            return False

    def _create_dummy_models(self):
        """Create dummy models for testing (when real models not available)"""
        from sklearn.ensemble import RandomForestClassifier, IsolationForest

        logger.info("Creating dummy models for testing...")

        # Dummy Random Forest (trained on random data)
        rf = RandomForestClassifier(n_estimators=10, random_state=42)
        X_dummy = np.random.randn(100, 78)
        y_dummy = np.random.randint(0, 2, 100)
        rf.fit(X_dummy, y_dummy)

        self.models['random_forest'] = {
            'model': rf,
            'weight': 0.5
        }

        # Dummy Isolation Forest
        iso_forest = IsolationForest(n_estimators=10, random_state=42)
        iso_forest.fit(X_dummy)

        self.models['isolation_forest'] = {
            'model': iso_forest,
            'weight': 0.5
        }

        logger.info("Dummy models created successfully")

    def preprocess_features(self, features: np.ndarray) -> np.ndarray:
        """
        Preprocess features (scaling, normalization)

        Args:
            features: Raw feature vector (78 features)

        Returns:
            Preprocessed features (2D array with shape (1, 78))
        """
        # Ensure features is 1D array
        if features.ndim > 1:
            features = features.flatten()

        # Handle NaN and inf values
        features = np.nan_to_num(features, nan=0.0, posinf=1e9, neginf=-1e9)

        # Reshape to 2D array (required by scikit-learn)
        features_2d = features.reshape(1, -1)

        # Apply scaling if scaler is available
        if self.scaler:
            features_2d = self.scaler.transform(features_2d)

        return features_2d

    def predict(self, features: np.ndarray) -> Tuple[bool, float, Dict]:
        """
        Predict if flow is anomalous

        Args:
            features: Feature vector (78 features)

        Returns:
            Tuple of (is_anomaly, confidence, details)
        """
        start_time = time.time()

        # Preprocess
        features_processed = self.preprocess_features(features)

        # Ensemble prediction
        predictions = {}
        scores = []

        for model_name, model_info in self.models.items():
            model = model_info['model']
            weight = model_info['weight']

            try:
                if hasattr(model, 'predict_proba'):
                    # Classification model (Random Forest, etc.)
                    pred = model.predict(features_processed)
                    proba = model.predict_proba(features_processed)[0]
                    anomaly_score = proba[1] if len(proba) > 1 else proba[0]
                elif hasattr(model, 'decision_function'):
                    # Isolation Forest
                    decision = model.decision_function(features_processed)[0]
                    # Convert to 0-1 score (negative = anomaly)
                    anomaly_score = 1.0 if decision < 0 else 0.0
                else:
                    pred = model.predict(features_processed)
                    anomaly_score = float(pred[0])

                predictions[model_name] = anomaly_score
                scores.append(anomaly_score * weight)

            except Exception as e:
                logger.error(f"Model {model_name} prediction failed: {e}")
                continue

        # Weighted ensemble score
        if scores:
            ensemble_score = sum(scores) / sum(m['weight'] for m in self.models.values())
        else:
            ensemble_score = 0.0

        # Decision
        threshold = self.config.get('threshold', 0.7)
        is_anomaly = ensemble_score >= threshold

        # Update stats
        inference_time = (time.time() - start_time) * 1000  # ms
        self.stats['total_flows'] += 1
        if is_anomaly:
            self.stats['anomalies_detected'] += 1
        else:
            self.stats['benign_flows'] += 1

        # Update average inference time
        n = self.stats['total_flows']
        self.stats['avg_inference_time_ms'] = (
            (self.stats['avg_inference_time_ms'] * (n - 1) + inference_time) / n
        )

        details = {
            'ensemble_score': float(ensemble_score),
            'threshold': threshold,
            'model_predictions': {k: float(v) for k, v in predictions.items()},
            'inference_time_ms': inference_time
        }

        return is_anomaly, ensemble_score, details

    def process_json_features(self, json_data: str) -> Tuple[bool, float, Dict]:
        """
        Process features from JSON (from NIDS)

        Args:
            json_data: JSON string with features

        Returns:
            Tuple of (is_anomaly, confidence, details)
        """
        try:
            data = json.loads(json_data)

            # Extract features in correct order
            features = []
            for feature_name in self.feature_names:
                features.append(data.get(feature_name, 0.0))

            features = np.array(features, dtype=np.float64)

            return self.predict(features)

        except Exception as e:
            logger.error(f"Failed to process JSON features: {e}")
            return False, 0.0, {'error': str(e)}

    def get_stats(self) -> Dict:
        """Get detector statistics"""
        return self.stats.copy()

    def print_stats(self):
        """Print statistics"""
        print("\n" + "="*50)
        print("  Anomaly Detector Statistics")
        print("="*50)
        print(f"Total Flows:          {self.stats['total_flows']}")
        print(f"Anomalies Detected:   {self.stats['anomalies_detected']}")
        print(f"Benign Flows:         {self.stats['benign_flows']}")
        if self.stats['total_flows'] > 0:
            anomaly_rate = (self.stats['anomalies_detected'] / self.stats['total_flows']) * 100
            print(f"Anomaly Rate:         {anomaly_rate:.2f}%")
        print(f"Avg Inference Time:   {self.stats['avg_inference_time_ms']:.2f} ms")
        print("="*50 + "\n")


def main():
    """Main function for standalone testing"""
    print("="*50)
    print("  AI Anomaly Detector - Standalone Mode")
    print("="*50)

    # Initialize detector
    detector = AnomalyDetector()

    # Load models
    if not detector.load_models():
        logger.error("Failed to load models")
        return 1

    print("\nDetector initialized successfully!")
    print("Ready to process features...\n")

    # Test with sample features (simulated)
    print("Running test with sample features...")

    # Generate 10 test flows
    for i in range(10):
        # Random features (in real use, these come from NIDS)
        test_features = np.random.randn(78)

        is_anomaly, confidence, details = detector.predict(test_features)

        status = "ANOMALY" if is_anomaly else "BENIGN"
        color = "\033[0;31m" if is_anomaly else "\033[0;32m"
        print(f"{color}[Flow {i+1:02d}] {status} (confidence: {confidence:.3f})\033[0m")

    # Print final statistics
    detector.print_stats()

    return 0


if __name__ == "__main__":
    sys.exit(main())

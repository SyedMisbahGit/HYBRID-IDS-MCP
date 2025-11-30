"""
SENTINEL | CORE - Unified Prediction Engine

NOTE: This engine handles all ML inference for the SIEM dashboard.
TODO: Add model versioning and hot-reload capability for production deployment.
TODO: Implement fallback to secondary models if primary fails.

Architecture:
- NIDS SIDS: Random Forest for multi-class attack classification
- NIDS A-IDS: Isolation Forest for anomaly detection
- HIDS: LSTM Autoencoder for system call sequence analysis
"""

import numpy as np
import joblib
import json
import os
import logging
from tensorflow import keras

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PredictionEngine:
    """
    Unified ML prediction engine for Hybrid IDS
    
    Loads and manages all trained models:
    - NIDS SIDS (Random Forest)
    - NIDS A-IDS (Isolation Forest)
    - HIDS (LSTM Autoencoder)
    """
    
    def __init__(self, models_dir=None):
        """
        Initialize prediction engine
        
        Args:
            models_dir: Base directory containing model subdirectories
        """
        if models_dir is None:
            # Resolve relative to this script
            base_dir = os.path.dirname(os.path.abspath(__file__))
            models_dir = os.path.join(base_dir, '../../models')
            
        self.models_dir = os.path.normpath(models_dir)
        
        # NIDS models
        self.nids_sids_model = None
        self.nids_aids_model = None
        self.nids_scaler = None
        self.nids_label_encoder = None
        self.nids_feature_names = None
        self.aids_threshold = None
        
        # HIDS models
        self.hids_model = None
        self.hids_encoder = None
        self.hids_threshold = None
        
        # Status flags
        self.nids_sids_loaded = False
        self.nids_aids_loaded = False
        self.hids_loaded = False
    
    def load_nids_sids(self):
        """Load NIDS SIDS (supervised classification) model"""
        try:
            logger.info("Loading NIDS SIDS model...")
            nids_dir = os.path.join(self.models_dir, 'nids')
            
            # Load model
            model_path = os.path.join(nids_dir, 'sids_rf.pkl')
            self.nids_sids_model = joblib.load(model_path)
            
            # Load scaler
            scaler_path = os.path.join(nids_dir, 'scaler.pkl')
            self.nids_scaler = joblib.load(scaler_path)
            
            # Load label encoder
            encoder_path = os.path.join(nids_dir, 'label_encoder.pkl')
            self.nids_label_encoder = joblib.load(encoder_path)
            
            # Load feature names
            features_path = os.path.join(nids_dir, 'feature_names.json')
            with open(features_path, 'r') as f:
                self.nids_feature_names = json.load(f)
            
            self.nids_sids_loaded = True
            logger.info("[SUCCESS] NIDS SIDS model loaded successfully")
            logger.info(f"   Classes: {self.nids_label_encoder.classes_}")
            
        except FileNotFoundError as e:
            logger.error(f"[!] CRITICAL: NIDS SIDS model files not found - {e}")
            logger.warning("[!] Run training script: python src/ml/nids/sids_trainer.py")
            self.nids_sids_loaded = False
        except Exception as e:
            logger.error(f"[!] CRITICAL FAILURE in NIDS SIDS loader: {e}")
            logger.warning("[!] Defaulting to Safe Mode (no SIDS predictions)")
            self.nids_sids_loaded = False
    
    def load_nids_aids(self):
        """Load NIDS A-IDS (anomaly detection) model"""
        try:
            logger.info("Loading NIDS A-IDS model...")
            nids_dir = os.path.join(self.models_dir, 'nids')
            
            # Load model
            model_path = os.path.join(nids_dir, 'aids_iforest.pkl')
            self.nids_aids_model = joblib.load(model_path)
            
            # Load threshold
            threshold_path = os.path.join(nids_dir, 'aids_threshold.json')
            with open(threshold_path, 'r') as f:
                self.aids_threshold = json.load(f)['threshold']
            
            self.nids_aids_loaded = True
            logger.info("[SUCCESS] NIDS A-IDS model loaded successfully")
            logger.info(f"   Anomaly threshold: {self.aids_threshold:.4f}")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to load NIDS A-IDS model: {e}")
            self.nids_aids_loaded = False
    
    def load_hids(self):
        """Load HIDS (LSTM sequence) model"""
        try:
            logger.info("Loading HIDS model...")
            hids_dir = os.path.join(self.models_dir, 'hids')
            
            # Load model
            model_path = os.path.join(hids_dir, 'lstm_autoencoder.h5')
            self.hids_model = keras.models.load_model(model_path)
            
            # Load encoder
            encoder_path = os.path.join(hids_dir, 'syscall_encoder.pkl')
            self.hids_encoder = joblib.load(encoder_path)
            
            # Load threshold
            threshold_path = os.path.join(hids_dir, 'threshold.json')
            with open(threshold_path, 'r') as f:
                self.hids_threshold = json.load(f)['threshold']
            
            self.hids_loaded = True
            logger.info("[SUCCESS] HIDS model loaded successfully")
            logger.info(f"   Anomaly threshold: {self.hids_threshold:.4f}")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to load HIDS model: {e}")
            self.hids_loaded = False
    
    def load_all(self):
        """Load all available models"""
        logger.info("="*60)
        logger.info("Loading all models...")
        logger.info("="*60)
        
        self.load_nids_sids()
        self.load_nids_aids()
        self.load_hids()
        
        logger.info("\n" + "="*60)
        logger.info("Model Loading Summary:")
        logger.info(f"  NIDS SIDS: {'[LOADED]' if self.nids_sids_loaded else '[NOT LOADED]'}")
        logger.info(f"  NIDS A-IDS: {'[LOADED]' if self.nids_aids_loaded else '[NOT LOADED]'}")
        logger.info(f"  HIDS: {'[LOADED]' if self.hids_loaded else '[NOT LOADED]'}")
        logger.info("="*60)
    
    def predict_nids(self, network_features):
        """
        Predict using both NIDS SIDS and A-IDS
        
        Args:
            network_features: Network flow features (78 CIC features)
                             Can be a single sample or batch
                             
        Returns:
            Dictionary with predictions from both models
        """
        if not self.nids_sids_loaded and not self.nids_aids_loaded:
            raise RuntimeError("No NIDS models loaded")
        
        # Ensure 2D array
        if len(network_features.shape) == 1:
            network_features = network_features.reshape(1, -1)
        
        # Scale features
        features_scaled = self.nids_scaler.transform(network_features)
        
        results = {}
        
        # SIDS prediction
        if self.nids_sids_loaded:
            sids_pred = self.nids_sids_model.predict(features_scaled)
            sids_proba = self.nids_sids_model.predict_proba(features_scaled)
            
            # Decode labels
            sids_labels = self.nids_label_encoder.inverse_transform(sids_pred)
            
            # Get confidence (max probability)
            sids_confidence = sids_proba.max(axis=1)
            
            results['sids'] = {
                'predictions': sids_labels.tolist(),
                'probabilities': sids_proba.tolist(),
                'confidence': sids_confidence.tolist()
            }
        
        # A-IDS prediction
        if self.nids_aids_loaded:
            aids_pred = self.nids_aids_model.predict(features_scaled)
            aids_scores = -self.nids_aids_model.decision_function(features_scaled)
            
            # Convert to binary (1 = anomaly, 0 = normal)
            aids_binary = (aids_pred == -1).astype(int)
            
            # Normalize scores to 0-1 range
            aids_scores_norm = np.clip(aids_scores / (self.aids_threshold * 2), 0, 1)
            
            results['aids'] = {
                'predictions': aids_binary.tolist(),
                'anomaly_scores': aids_scores.tolist(),
                'anomaly_scores_normalized': aids_scores_norm.tolist(),
                'is_anomaly': (aids_scores > self.aids_threshold).tolist()
            }
        
        return results
    
    def predict_hids(self, syscall_sequence):
        """
        Predict using HIDS LSTM model
        
        Args:
            syscall_sequence: System call sequence (encoded integers)
                             Can be a single sequence or batch
                             
        Returns:
            Dictionary with predictions
        """
        if not self.hids_loaded:
            raise RuntimeError("HIDS model not loaded")
        
        # Ensure 2D array
        if len(syscall_sequence.shape) == 1:
            syscall_sequence = syscall_sequence.reshape(1, -1)
        
        # Predict (reconstruction)
        predictions = self.hids_model.predict(syscall_sequence, verbose=0)
        
        # Calculate reconstruction error
        errors = []
        for i in range(len(syscall_sequence)):
            actual = syscall_sequence[i]
            predicted = predictions[i]
            
            error = 0
            for j, syscall in enumerate(actual):
                if syscall < predicted.shape[1]:
                    error += -np.log(predicted[j, syscall] + 1e-10)
            
            errors.append(error / len(actual))
        
        errors = np.array(errors)
        
        # Determine if anomaly
        is_anomaly = errors > self.hids_threshold
        
        # Normalize scores to 0-1 range
        errors_norm = np.clip(errors / (self.hids_threshold * 2), 0, 1)
        
        return {
            'reconstruction_errors': errors.tolist(),
            'reconstruction_errors_normalized': errors_norm.tolist(),
            'is_anomaly': is_anomaly.tolist(),
            'predictions': is_anomaly.astype(int).tolist()
        }
    
    def get_status(self):
        """Get status of all models"""
        return {
            'nids_sids': self.nids_sids_loaded,
            'nids_aids': self.nids_aids_loaded,
            'hids': self.hids_loaded
        }


# Example usage
if __name__ == "__main__":
    # Initialize engine
    engine = PredictionEngine(models_dir='../models')
    
    # Load all models
    engine.load_all()
    
    # Check status
    status = engine.get_status()
    print(f"\nModel Status: {status}")
    
    # Example NIDS prediction (if models are loaded)
    if engine.nids_sids_loaded or engine.nids_aids_loaded:
        print("\n" + "="*60)
        print("Example NIDS Prediction:")
        print("="*60)
        
        # Create dummy features (78 features)
        dummy_features = np.random.randn(1, 78)
        
        try:
            nids_results = engine.predict_nids(dummy_features)
            
            if 'sids' in nids_results:
                print(f"\nSIDS Prediction: {nids_results['sids']['predictions'][0]}")
                print(f"SIDS Confidence: {nids_results['sids']['confidence'][0]:.4f}")
            
            if 'aids' in nids_results:
                print(f"\nA-IDS Anomaly: {nids_results['aids']['is_anomaly'][0]}")
                print(f"A-IDS Score: {nids_results['aids']['anomaly_scores'][0]:.4f}")
        except Exception as e:
            print(f"Error: {e}")
    
    # Example HIDS prediction (if model is loaded)
    if engine.hids_loaded:
        print("\n" + "="*60)
        print("Example HIDS Prediction:")
        print("="*60)
        
        # Create dummy sequence (100 syscalls)
        dummy_sequence = np.random.randint(0, 100, size=(1, 100))
        
        try:
            hids_results = engine.predict_hids(dummy_sequence)
            
            print(f"\nHIDS Anomaly: {hids_results['is_anomaly'][0]}")
            print(f"HIDS Error: {hids_results['reconstruction_errors'][0]:.4f}")
        except Exception as e:
            print(f"Error: {e}")

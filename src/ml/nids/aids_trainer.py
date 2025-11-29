"""
A-IDS Trainer - Anomaly-based Intrusion Detection System

Trains an Isolation Forest on BENIGN traffic only from CIC-IDS2017
to detect anomalies (attacks) as deviations from normal behavior.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import joblib
import json
import os
import logging
from data_loader import CICIDS2017Loader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIDSTrainer:
    """
    Train A-IDS (Anomaly-based IDS) using unsupervised learning
    """
    
    def __init__(self, model_dir='../../models/nids'):
        """
        Initialize trainer
        
        Args:
            model_dir: Directory to save trained models
        """
        self.model_dir = model_dir
        self.model = None
        self.scaler = None
        self.threshold = None
        
        # Create model directory if it doesn't exist
        os.makedirs(model_dir, exist_ok=True)
    
    def train(self, X_train_benign, contamination=0.01, random_state=42):
        """
        Train Isolation Forest on benign traffic only
        
        Args:
            X_train_benign: Training features (BENIGN traffic only)
            contamination: Expected proportion of outliers
            random_state: Random seed
        """
        logger.info("Training A-IDS Isolation Forest...")
        logger.info(f"Parameters: contamination={contamination}")
        logger.info(f"Training samples (benign only): {len(X_train_benign)}")
        
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100,
            max_samples='auto',
            n_jobs=-1,
            verbose=1
        )
        
        self.model.fit(X_train_benign)
        logger.info("✅ Training complete!")
    
    def evaluate(self, X_test, y_test_binary):
        """
        Evaluate model on test set
        
        Args:
            X_test: Test features
            y_test_binary: Test labels (0=Benign, 1=Attack)
            
        Returns:
            Dictionary with evaluation metrics
        """
        logger.info("Evaluating A-IDS model...")
        
        # Get anomaly scores
        # Isolation Forest returns: -1 for outliers, 1 for inliers
        # We convert to: 1 for outliers (attacks), 0 for inliers (benign)
        predictions = self.model.predict(X_test)
        predictions_binary = (predictions == -1).astype(int)
        
        # Get anomaly scores (decision function)
        # Lower scores = more anomalous
        anomaly_scores = -self.model.decision_function(X_test)
        
        # Calculate metrics
        accuracy = (predictions_binary == y_test_binary).mean()
        logger.info(f"Accuracy: {accuracy:.4f}")
        
        # ROC-AUC
        try:
            roc_auc = roc_auc_score(y_test_binary, anomaly_scores)
            logger.info(f"ROC-AUC: {roc_auc:.4f}")
        except:
            roc_auc = None
            logger.warning("Could not calculate ROC-AUC")
        
        # Classification report
        report = classification_report(
            y_test_binary, 
            predictions_binary,
            target_names=['Benign', 'Attack']
        )
        logger.info(f"\nClassification Report:\n{report}")
        
        # Confusion matrix
        cm = confusion_matrix(y_test_binary, predictions_binary)
        logger.info(f"\nConfusion Matrix:\n{cm}")
        
        # Calculate optimal threshold
        self.threshold = np.percentile(anomaly_scores[y_test_binary == 0], 95)
        logger.info(f"Anomaly threshold (95th percentile of benign): {self.threshold:.4f}")
        
        return {
            'accuracy': accuracy,
            'roc_auc': roc_auc,
            'classification_report': report,
            'confusion_matrix': cm.tolist(),
            'threshold': self.threshold,
            'anomaly_scores_stats': {
                'mean': float(anomaly_scores.mean()),
                'std': float(anomaly_scores.std()),
                'min': float(anomaly_scores.min()),
                'max': float(anomaly_scores.max())
            }
        }
    
    def save(self, scaler):
        """
        Save trained model and preprocessing objects
        
        Args:
            scaler: Fitted StandardScaler
        """
        logger.info(f"Saving A-IDS model to {self.model_dir}...")
        
        # Save model
        model_path = os.path.join(self.model_dir, 'aids_iforest.pkl')
        joblib.dump(self.model, model_path)
        logger.info(f"✅ Model saved: {model_path}")
        
        # Save scaler (same as SIDS, but save separately for A-IDS independence)
        scaler_path = os.path.join(self.model_dir, 'aids_scaler.pkl')
        joblib.dump(scaler, scaler_path)
        logger.info(f"✅ Scaler saved: {scaler_path}")
        
        # Save threshold
        threshold_path = os.path.join(self.model_dir, 'aids_threshold.json')
        with open(threshold_path, 'w') as f:
            json.dump({'threshold': float(self.threshold)}, f, indent=2)
        logger.info(f"✅ Threshold saved: {threshold_path}")
    
    def load(self):
        """Load trained model and preprocessing objects"""
        logger.info(f"Loading A-IDS model from {self.model_dir}...")
        
        model_path = os.path.join(self.model_dir, 'aids_iforest.pkl')
        self.model = joblib.load(model_path)
        
        scaler_path = os.path.join(self.model_dir, 'aids_scaler.pkl')
        self.scaler = joblib.load(scaler_path)
        
        threshold_path = os.path.join(self.model_dir, 'aids_threshold.json')
        with open(threshold_path, 'r') as f:
            self.threshold = json.load(f)['threshold']
        
        logger.info("✅ Model loaded successfully!")
    
    def predict(self, X):
        """
        Predict anomalies
        
        Args:
            X: Features (scaled)
            
        Returns:
            predictions (0=benign, 1=attack), anomaly_scores
        """
        predictions = self.model.predict(X)
        predictions_binary = (predictions == -1).astype(int)
        anomaly_scores = -self.model.decision_function(X)
        return predictions_binary, anomaly_scores


# Main training script
if __name__ == "__main__":
    logger.info("="*60)
    logger.info("A-IDS Training Script - CIC-IDS2017")
    logger.info("="*60)
    
    # Load data (auto-detects real or mock data)
    loader = CICIDS2017Loader()
    
    try:
        # Load dataset
        logger.info("\nStep 1: Loading dataset...")
        data = loader.load_data(sample_size=50000)  # Use 50k samples for faster training
        
        # Preprocess
        logger.info("\nStep 2: Preprocessing...")
        X, y = loader.preprocess(data)
        
        # Prepare for A-IDS (benign only for training)
        logger.info("\nStep 3: Preparing data for A-IDS...")
        X_train_benign, X_test, y_test_binary = loader.prepare_for_aids(X, y)
        
        # Train model
        logger.info("\nStep 4: Training A-IDS model...")
        trainer = AIDSTrainer()
        trainer.train(X_train_benign, contamination=0.01)
        
        # Evaluate
        logger.info("\nStep 5: Evaluating model...")
        metrics = trainer.evaluate(X_test, y_test_binary)
        
        # Save
        logger.info("\nStep 6: Saving model...")
        trainer.save(scaler=loader.get_scaler())
        
        logger.info("\n" + "="*60)
        logger.info("✅ A-IDS Training Complete!")
        logger.info(f"Final Accuracy: {metrics['accuracy']:.4f}")
        if metrics['roc_auc']:
            logger.info(f"ROC-AUC: {metrics['roc_auc']:.4f}")
        logger.info("="*60)
        
    except FileNotFoundError as e:
        logger.error(f"\n❌ Error: {e}")
        logger.error("Please download CIC-IDS2017 dataset and place CSV files in data/raw/cicids2017/")
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        raise

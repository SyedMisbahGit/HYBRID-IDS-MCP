"""
SIDS Trainer - Supervised Intrusion Detection System

Trains a Random Forest classifier on CIC-IDS2017 dataset
to classify network traffic into specific attack types.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
import json
import os
import logging
from data_loader import CICIDS2017Loader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SIDSTrainer:
    """
    Train SIDS (Signature-based IDS) using supervised learning
    """
    
    def __init__(self, model_dir=None):
        """
        Initialize trainer
        
        Args:
            model_dir: Directory to save trained models
        """
        if model_dir is None:
            # Resolve relative to this script
            base_dir = os.path.dirname(os.path.abspath(__file__))
            model_dir = os.path.join(base_dir, '../../../models/nids')
            
        self.model_dir = os.path.normpath(model_dir)
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.feature_names = None
        
        # Create model directory if it doesn't exist
        os.makedirs(self.model_dir, exist_ok=True)
    
    def train(self, X_train, y_train, n_estimators=100, max_depth=20, random_state=42):
        """
        Train Random Forest classifier
        
        Args:
            X_train: Training features
            y_train: Training labels (encoded)
            n_estimators: Number of trees
            max_depth: Maximum tree depth
            random_state: Random seed
        """
        logger.info("Training SIDS Random Forest classifier...")
        logger.info(f"Parameters: n_estimators={n_estimators}, max_depth={max_depth}")
        
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1,
            verbose=1
        )
        
        self.model.fit(X_train, y_train)
        logger.info("✅ Training complete!")
    
    def evaluate(self, X_test, y_test, label_encoder):
        """
        Evaluate model on test set
        
        Args:
            X_test: Test features
            y_test: Test labels (encoded)
            label_encoder: Label encoder for decoding
            
        Returns:
            Dictionary with evaluation metrics
        """
        logger.info("Evaluating SIDS model...")
        
        # Predictions
        y_pred = self.model.predict(X_test)
        
        # Accuracy
        accuracy = accuracy_score(y_test, y_pred)
        logger.info(f"Accuracy: {accuracy:.4f}")
        
        # Classification report
        class_names = label_encoder.classes_
        report = classification_report(y_test, y_pred, target_names=class_names)
        logger.info(f"\nClassification Report:\n{report}")
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        logger.info(f"\nConfusion Matrix:\n{cm}")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        logger.info(f"\nTop 10 Important Features:\n{feature_importance.head(10)}")
        
        return {
            'accuracy': accuracy,
            'classification_report': report,
            'confusion_matrix': cm.tolist(),
            'feature_importance': feature_importance.to_dict('records')
        }
    
    def save(self, scaler, label_encoder, feature_names):
        """
        Save trained model and preprocessing objects
        
        Args:
            scaler: Fitted StandardScaler
            label_encoder: Fitted LabelEncoder
            feature_names: List of feature names
        """
        logger.info(f"Saving SIDS model to {self.model_dir}...")
        
        # Save model
        model_path = os.path.join(self.model_dir, 'sids_rf.pkl')
        joblib.dump(self.model, model_path)
        logger.info(f"✅ Model saved: {model_path}")
        
        # Save scaler
        scaler_path = os.path.join(self.model_dir, 'scaler.pkl')
        joblib.dump(scaler, scaler_path)
        logger.info(f"✅ Scaler saved: {scaler_path}")
        
        # Save label encoder
        encoder_path = os.path.join(self.model_dir, 'label_encoder.pkl')
        joblib.dump(label_encoder, encoder_path)
        logger.info(f"✅ Label encoder saved: {encoder_path}")
        
        # Save feature names
        features_path = os.path.join(self.model_dir, 'feature_names.json')
        with open(features_path, 'w') as f:
            json.dump(feature_names, f, indent=2)
        logger.info(f"✅ Feature names saved: {features_path}")
    
    def load(self):
        """Load trained model and preprocessing objects"""
        logger.info(f"Loading SIDS model from {self.model_dir}...")
        
        model_path = os.path.join(self.model_dir, 'sids_rf.pkl')
        self.model = joblib.load(model_path)
        
        scaler_path = os.path.join(self.model_dir, 'scaler.pkl')
        self.scaler = joblib.load(scaler_path)
        
        encoder_path = os.path.join(self.model_dir, 'label_encoder.pkl')
        self.label_encoder = joblib.load(encoder_path)
        
        features_path = os.path.join(self.model_dir, 'feature_names.json')
        with open(features_path, 'r') as f:
            self.feature_names = json.load(f)
        
        logger.info("✅ Model loaded successfully!")
    
    def predict(self, X):
        """
        Predict attack types
        
        Args:
            X: Features (scaled)
            
        Returns:
            predictions, probabilities
        """
        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)
        return predictions, probabilities


# Main training script
if __name__ == "__main__":
    logger.info("="*60)
    logger.info("SIDS Training Script - CIC-IDS2017")
    logger.info("="*60)
    
    # Load data (auto-detects real or mock data)
    loader = CICIDS2017Loader()
    
    try:
        # Step 1: Check for Sampled Data (Big Data Solution)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        sampled_data_path = os.path.join(base_dir, '../../../data/processed/train_nids_sampled.csv')
        
        if os.path.exists(sampled_data_path):
            logger.info("\nStep 1: Loading SMART SAMPLED dataset (High Accuracy Mode)...")
            data = loader.load_processed_data(sampled_data_path)
        else:
            # Fallback to standard loading (Mock or Raw)
            logger.info("\nStep 1: Loading dataset (Standard Mode)...")
            data = loader.load_data(sample_size=50000)
            
            # Check if using mock data
            if 'mock' in str(loader.data_dir).lower() or any('mock' in str(f).lower() for f in os.listdir(loader.data_dir) if f.endswith('.csv')):
                logger.warning("\n" + "="*60)
                logger.warning("⚠️  WARNING: TRAINING ON MOCK DATA")
                logger.warning("="*60)
                logger.warning("Mock data is synthetic and will produce RANDOM results.")
                logger.warning("Model accuracy will be meaningless.")
                logger.warning("For real results, download CIC-IDS2017:")
                logger.warning("  python scripts/download_instructions.py")
                logger.warning("="*60 + "\n")
        
        # Preprocess
        logger.info("\nStep 2: Preprocessing...")
        X, y = loader.preprocess(data)
        
        # Prepare for SIDS
        logger.info("\nStep 3: Preparing data for SIDS...")
        X_train, X_test, y_train, y_test = loader.prepare_for_sids(X, y)
        
        # Train model
        logger.info("\nStep 4: Training SIDS model...")
        trainer = SIDSTrainer()
        trainer.feature_names = loader.get_feature_names()
        trainer.train(X_train, y_train, n_estimators=100, max_depth=20)
        
        # Evaluate
        logger.info("\nStep 5: Evaluating model...")
        metrics = trainer.evaluate(X_test, y_test, loader.get_label_encoder())
        
        # Save Performance Report
        report_path = os.path.join(base_dir, '../../../models/performance_report.txt')
        with open(report_path, 'w') as f:
            f.write("="*60 + "\n")
            f.write("HYBRID IDS - MODEL PERFORMANCE REPORT\n")
            f.write("="*60 + "\n\n")
            f.write(f"Model: NIDS SIDS (Random Forest)\n")
            f.write(f"Accuracy: {metrics['accuracy']:.4f}\n\n")
            f.write("Classification Report:\n")
            f.write(metrics['classification_report'])
            f.write("\n" + "="*60 + "\n")
        logger.info(f"✅ Performance report saved to {report_path}")
        
        # Save
        logger.info("\nStep 6: Saving model...")
        trainer.save(
            scaler=loader.get_scaler(),
            label_encoder=loader.get_label_encoder(),
            feature_names=loader.get_feature_names()
        )
        
        logger.info("\n" + "="*60)
        logger.info("✅ SIDS Training Complete!")
        logger.info(f"Final Accuracy: {metrics['accuracy']:.4f}")
        logger.info("="*60)
        
    except FileNotFoundError as e:
        logger.error(f"\n❌ Error: {e}")
        logger.error("Please download CIC-IDS2017 dataset and place CSV files in data/raw/cicids2017/")
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        raise

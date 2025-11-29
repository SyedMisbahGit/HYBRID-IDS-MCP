"""
HIDS Sequence Trainer - LSTM Autoencoder

Trains an LSTM autoencoder on normal system call sequences
to detect anomalous behavior.
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import joblib
import json
import os
import logging
from data_loader import ADFALDLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HIDSSequenceTrainer:
    """
    Train HIDS using LSTM Autoencoder for sequence anomaly detection
    """
    
    def __init__(self, model_dir='../../models/hids'):
        """
        Initialize trainer
        
        Args:
            model_dir: Directory to save trained models
        """
        self.model_dir = model_dir
        self.model = None
        self.threshold = None
        
        # Create model directory if it doesn't exist
        os.makedirs(model_dir, exist_ok=True)
    
    def build_model(self, vocab_size, sequence_length, embedding_dim=32, lstm_units=64):
        """
        Build LSTM Autoencoder model
        
        Args:
            vocab_size: Number of unique system calls
            sequence_length: Length of input sequences
            embedding_dim: Dimension of embedding layer
            lstm_units: Number of LSTM units
            
        Returns:
            Compiled Keras model
        """
        logger.info("Building LSTM Autoencoder...")
        logger.info(f"Vocab size: {vocab_size}, Sequence length: {sequence_length}")
        logger.info(f"Embedding dim: {embedding_dim}, LSTM units: {lstm_units}")
        
        # Encoder
        encoder_inputs = layers.Input(shape=(sequence_length,))
        x = layers.Embedding(vocab_size + 1, embedding_dim)(encoder_inputs)
        x = layers.LSTM(lstm_units, return_sequences=False)(x)
        encoder_outputs = layers.RepeatVector(sequence_length)(x)
        
        # Decoder
        x = layers.LSTM(lstm_units, return_sequences=True)(encoder_outputs)
        decoder_outputs = layers.TimeDistributed(layers.Dense(vocab_size + 1, activation='softmax'))(x)
        
        # Autoencoder model
        model = keras.Model(encoder_inputs, decoder_outputs)
        
        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        logger.info(f"\nModel Summary:")
        model.summary(print_fn=logger.info)
        
        return model
    
    def train(self, X_train, y_train, vocab_size, epochs=20, batch_size=64, validation_split=0.2):
        """
        Train LSTM Autoencoder on NORMAL sequences only
        
        Args:
            X_train: Training sequences
            y_train: Training labels (0=normal, 1=attack)
            vocab_size: Vocabulary size
            epochs: Number of training epochs
            batch_size: Batch size
            validation_split: Validation split
        """
        logger.info("Training HIDS LSTM Autoencoder...")
        
        # Filter only normal sequences for training
        X_train_normal = X_train[y_train == 0]
        logger.info(f"Training on {len(X_train_normal)} normal sequences")
        
        # Build model
        sequence_length = X_train_normal.shape[1]
        self.model = self.build_model(vocab_size, sequence_length)
        
        # Prepare target (same as input for autoencoder)
        # Expand dims for sparse_categorical_crossentropy
        y_train_autoencoder = np.expand_dims(X_train_normal, -1)
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=5,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=3
            )
        ]
        
        # Train
        history = self.model.fit(
            X_train_normal,
            y_train_autoencoder,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=1
        )
        
        logger.info("✅ Training complete!")
        return history
    
    def calculate_reconstruction_error(self, X):
        """
        Calculate reconstruction error for sequences
        
        Args:
            X: Input sequences
            
        Returns:
            Reconstruction errors
        """
        # Predict
        predictions = self.model.predict(X, verbose=0)
        
        # Calculate reconstruction error (cross-entropy)
        errors = []
        for i in range(len(X)):
            # Get predicted probabilities for actual syscalls
            actual_syscalls = X[i]
            predicted_probs = predictions[i]
            
            # Calculate negative log likelihood
            error = 0
            for j, syscall in enumerate(actual_syscalls):
                if syscall < predicted_probs.shape[1]:
                    error += -np.log(predicted_probs[j, syscall] + 1e-10)
            
            errors.append(error / len(actual_syscalls))
        
        return np.array(errors)
    
    def evaluate(self, X_test, y_test):
        """
        Evaluate model on test set
        
        Args:
            X_test: Test sequences
            y_test: Test labels (0=normal, 1=attack)
            
        Returns:
            Dictionary with evaluation metrics
        """
        logger.info("Evaluating HIDS model...")
        
        # Calculate reconstruction errors
        errors = self.calculate_reconstruction_error(X_test)
        
        # Calculate threshold (95th percentile of normal errors)
        normal_errors = errors[y_test == 0]
        self.threshold = np.percentile(normal_errors, 95)
        logger.info(f"Anomaly threshold (95th percentile): {self.threshold:.4f}")
        
        # Predict anomalies (error > threshold)
        predictions = (errors > self.threshold).astype(int)
        
        # Calculate metrics
        accuracy = (predictions == y_test).mean()
        logger.info(f"Accuracy: {accuracy:.4f}")
        
        # ROC-AUC
        try:
            roc_auc = roc_auc_score(y_test, errors)
            logger.info(f"ROC-AUC: {roc_auc:.4f}")
        except:
            roc_auc = None
            logger.warning("Could not calculate ROC-AUC")
        
        # Classification report
        report = classification_report(
            y_test,
            predictions,
            target_names=['Normal', 'Attack']
        )
        logger.info(f"\nClassification Report:\n{report}")
        
        # Confusion matrix
        cm = confusion_matrix(y_test, predictions)
        logger.info(f"\nConfusion Matrix:\n{cm}")
        
        return {
            'accuracy': accuracy,
            'roc_auc': roc_auc,
            'classification_report': report,
            'confusion_matrix': cm.tolist(),
            'threshold': float(self.threshold),
            'error_stats': {
                'mean': float(errors.mean()),
                'std': float(errors.std()),
                'min': float(errors.min()),
                'max': float(errors.max())
            }
        }
    
    def save(self, syscall_encoder):
        """
        Save trained model and preprocessing objects
        
        Args:
            syscall_encoder: Fitted LabelEncoder for system calls
        """
        logger.info(f"Saving HIDS model to {self.model_dir}...")
        
        # Save model
        model_path = os.path.join(self.model_dir, 'lstm_autoencoder.h5')
        self.model.save(model_path)
        logger.info(f"✅ Model saved: {model_path}")
        
        # Save encoder
        encoder_path = os.path.join(self.model_dir, 'syscall_encoder.pkl')
        joblib.dump(syscall_encoder, encoder_path)
        logger.info(f"✅ Encoder saved: {encoder_path}")
        
        # Save threshold
        threshold_path = os.path.join(self.model_dir, 'threshold.json')
        with open(threshold_path, 'w') as f:
            json.dump({'threshold': float(self.threshold)}, f, indent=2)
        logger.info(f"✅ Threshold saved: {threshold_path}")
    
    def load(self):
        """Load trained model and preprocessing objects"""
        logger.info(f"Loading HIDS model from {self.model_dir}...")
        
        model_path = os.path.join(self.model_dir, 'lstm_autoencoder.h5')
        self.model = keras.models.load_model(model_path)
        
        threshold_path = os.path.join(self.model_dir, 'threshold.json')
        with open(threshold_path, 'r') as f:
            self.threshold = json.load(f)['threshold']
        
        logger.info("✅ Model loaded successfully!")
    
    def predict(self, X):
        """
        Predict anomalies
        
        Args:
            X: Sequences
            
        Returns:
            predictions (0=normal, 1=attack), reconstruction_errors
        """
        errors = self.calculate_reconstruction_error(X)
        predictions = (errors > self.threshold).astype(int)
        return predictions, errors


# Main training script
if __name__ == "__main__":
    logger.info("="*60)
    logger.info("HIDS Training Script - ADFA-LD")
    logger.info("="*60)
    
    # Load data (auto-detects real or mock data)
    loader = ADFALDLoader()
    
    try:
        # Prepare data
        logger.info("\nStep 1: Loading and preparing data...")
        X_train, X_test, y_train, y_test = loader.prepare_data(
            window_size=100,
            stride=50
        )
        
        vocab_size = loader.get_vocab_size()
        logger.info(f"Vocabulary size: {vocab_size}")
        
        # Train model
        logger.info("\nStep 2: Training HIDS model...")
        trainer = HIDSSequenceTrainer()
        history = trainer.train(
            X_train, y_train,
            vocab_size=vocab_size,
            epochs=20,
            batch_size=64
        )
        
        # Evaluate
        logger.info("\nStep 3: Evaluating model...")
        metrics = trainer.evaluate(X_test, y_test)
        
        # Save
        logger.info("\nStep 4: Saving model...")
        trainer.save(syscall_encoder=loader.get_encoder())
        
        logger.info("\n" + "="*60)
        logger.info("✅ HIDS Training Complete!")
        logger.info(f"Final Accuracy: {metrics['accuracy']:.4f}")
        if metrics['roc_auc']:
            logger.info(f"ROC-AUC: {metrics['roc_auc']:.4f}")
        logger.info("="*60)
        
    except FileNotFoundError as e:
        logger.error(f"\n❌ Error: {e}")
        logger.error("Please download ADFA-LD dataset and extract to data/raw/adfa-ld/")
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        raise

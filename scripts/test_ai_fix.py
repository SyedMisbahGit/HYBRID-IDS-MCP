#!/usr/bin/env python3
"""
Quick test to verify the AI engine fix
Tests that the anomaly detector works without errors
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'ai', 'inference'))

import numpy as np
from anomaly_detector import AnomalyDetector

def test_anomaly_detector():
    """Test the anomaly detector with various inputs"""

    print("="*60)
    print("  Testing AI Anomaly Detector Fix")
    print("="*60)
    print()

    # Initialize detector
    print("[1/5] Initializing detector...")
    detector = AnomalyDetector()

    # Load models (will create dummy models)
    print("[2/5] Loading models...")
    if not detector.load_models():
        print("ERROR: Failed to load models!")
        return False
    print("✓ Models loaded successfully")
    print()

    # Test with 1D array
    print("[3/5] Testing with 1D array (78 features)...")
    features_1d = np.random.randn(78)
    try:
        is_anomaly, confidence, details = detector.predict(features_1d)
        print(f"✓ 1D array test passed!")
        print(f"  Result: {'ANOMALY' if is_anomaly else 'BENIGN'} (confidence: {confidence:.3f})")
        print(f"  Inference time: {details['inference_time_ms']:.2f} ms")
    except Exception as e:
        print(f"✗ 1D array test FAILED: {e}")
        return False
    print()

    # Test with 2D array (single sample)
    print("[4/5] Testing with 2D array (1, 78)...")
    features_2d = np.random.randn(1, 78)
    try:
        is_anomaly, confidence, details = detector.predict(features_2d)
        print(f"✓ 2D array test passed!")
        print(f"  Result: {'ANOMALY' if is_anomaly else 'BENIGN'} (confidence: {confidence:.3f})")
    except Exception as e:
        print(f"✗ 2D array test FAILED: {e}")
        return False
    print()

    # Test multiple predictions
    print("[5/5] Testing multiple predictions...")
    for i in range(5):
        features = np.random.randn(78)
        is_anomaly, confidence, details = detector.predict(features)
        status = "ANOMALY" if is_anomaly else "BENIGN"
        print(f"  Flow {i+1}: {status} (confidence: {confidence:.3f})")
    print()

    # Show statistics
    detector.print_stats()

    print("="*60)
    print("  ✓ ALL TESTS PASSED!")
    print("="*60)
    print()
    print("The AI engine is working correctly!")
    print("You can now run:")
    print("  python src/ai/inference/anomaly_detector.py")
    print("  python src/ai/inference/zmq_subscriber.py --simulate")
    print()

    return True


if __name__ == "__main__":
    try:
        success = test_anomaly_detector()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

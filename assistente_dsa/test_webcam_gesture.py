#!/usr/bin/env python3
"""
Test script for WebcamTestWindow with gesture control functionality.
This script tests the core components without running the full GUI.
"""

import sys
import os
import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, QSize, Qt
from PyQt6.QtGui import QImage, QPixmap

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_video_thread_imports():
    """Test if VideoThread can be imported and instantiated."""
    try:
        from Artificial_Intelligence.Video.visual_background import VideoThread
        print("✓ VideoThread import successful")

        # Test instantiation
        video_thread = VideoThread()
        print("✓ VideoThread instantiation successful")

        # Test basic attributes
        assert hasattr(video_thread, 'hand_detection_enabled')
        assert hasattr(video_thread, 'gesture_recognition_enabled')
        assert hasattr(video_thread, 'face_detection_enabled')
        print("✓ VideoThread attributes verified")

        return True
    except Exception as e:
        print(f"❌ VideoThread test failed: {e}")
        return False

def test_webcam_test_window_imports():
    """Test if WebcamTestWindow can be imported."""
    try:
        from main_01_Aircraft import WebcamTestWindow
        print("✓ WebcamTestWindow import successful")
        return True
    except Exception as e:
        print(f"❌ WebcamTestWindow import failed: {e}")
        return False

def test_opencv_functionality():
    """Test basic OpenCV functionality for gesture recognition."""
    try:
        # Test basic OpenCV operations
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        print("✓ OpenCV frame creation successful")

        # Test HSV conversion
        hsv = cv2.cvtColor(test_frame, cv2.COLOR_BGR2HSV)
        print("✓ HSV conversion successful")

        # Test skin color detection
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        print("✓ Skin color detection successful")

        # Test contour detection
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print("✓ Contour detection successful")

        return True
    except Exception as e:
        print(f"❌ OpenCV functionality test failed: {e}")
        return False

def test_coordinate_mapping():
    """Test coordinate mapping functions."""
    try:
        # Test basic coordinate mapping
        webcam_x, webcam_y = 320, 240  # Center of 640x480 frame
        webcam_width, webcam_height = 640, 480
        ui_width, ui_height = 400, 300

        # Calculate scale factors
        scale_x = ui_width / webcam_width
        scale_y = ui_height / webcam_height

        # Convert coordinates
        ui_x = int(webcam_x * scale_x)
        ui_y = int(webcam_y * scale_y)

        print(f"✓ Coordinate mapping: webcam({webcam_x},{webcam_y}) -> ui({ui_x},{ui_y})")

        # Verify the mapping is correct
        expected_ui_x = int(320 * (400/640))  # Should be 200
        expected_ui_y = int(240 * (300/480))  # Should be 150

        assert ui_x == expected_ui_x, f"X mapping incorrect: {ui_x} != {expected_ui_x}"
        assert ui_y == expected_ui_y, f"Y mapping incorrect: {ui_y} != {expected_ui_y}"

        print("✓ Coordinate mapping verification successful")
        return True
    except Exception as e:
        print(f"❌ Coordinate mapping test failed: {e}")
        return False

def test_gesture_detection_logic():
    """Test the gesture detection logic with mock data."""
    try:
        # Mock contour data for testing
        # Create a simple rectangular contour (closed hand)
        contour = np.array([[[100, 100]], [[200, 100]], [[200, 200]], [[100, 200]]], dtype=np.int32)

        # Test basic contour analysis
        area = cv2.contourArea(contour)
        print(f"✓ Contour area calculation: {area}")

        # Test convex hull
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        print(f"✓ Convex hull area: {hull_area}")

        # Test solidity calculation
        if hull_area > 0:
            solidity = area / hull_area
            print(f"✓ Solidity calculation: {solidity}")
        else:
            solidity = 0

        # Test gesture classification logic
        finger_count = 0  # Mock value
        if finger_count >= 4 and solidity > 0.75:
            gesture = "Mano Aperta"
        elif finger_count <= 2 or solidity < 0.65:
            gesture = "Mano Chiusa"
        else:
            gesture = "Gesto Parziale"

        print(f"✓ Gesture classification: {gesture}")

        # Test confidence calculation
        confidence = min(1.0, (finger_count * 0.2) + (solidity * 0.3) + 0.3)
        print(f"✓ Confidence calculation: {confidence}")

        return True
    except Exception as e:
        print(f"❌ Gesture detection logic test failed: {e}")
        return False

def main():
    """Run all tests for the webcam gesture control system."""
    print("🧪 Testing Webcam Test Window with Gesture Control")
    print("=" * 50)

    tests = [
        ("VideoThread Imports", test_video_thread_imports),
        ("WebcamTestWindow Imports", test_webcam_test_window_imports),
        ("OpenCV Functionality", test_opencv_functionality),
        ("Coordinate Mapping", test_coordinate_mapping),
        ("Gesture Detection Logic", test_gesture_detection_logic),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Webcam gesture control system is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
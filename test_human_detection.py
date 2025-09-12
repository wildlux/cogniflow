#!/usr/bin/env python3
"""
Test script for human detection (LIDAR-like) functionality.
Tests the contour-based human detection system.
"""

import sys
import os
import cv2
import numpy as np
import math

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

def test_human_detection():
    """Test the human detection algorithm with sample image processing."""
    print("🧪 Testing Human Detection (LIDAR-like) System")
    print("=" * 50)

    # Test parameters (same as in VideoThread)
    human_min_area = 10000
    human_max_area = 300000
    human_min_aspect = 0.3
    human_max_aspect = 1.2

    print(f"Test Parameters:")
    print(f"  - Min Area: {human_min_area}")
    print(f"  - Max Area: {human_max_area}")
    print(f"  - Min Aspect Ratio: {human_min_aspect}")
    print(f"  - Max Aspect Ratio: {human_max_aspect}")
    print()

    # Test contour analysis functions
    def analyze_contour_for_human(contour):
        """Analyze a contour to determine if it represents a human."""
        area = cv2.contourArea(contour)

        # Check area
        if not (human_min_area < area < human_max_area):
            return False, "Area out of range"

        # Get bounding box
        x, y, w, h = cv2.boundingRect(contour)

        # Check aspect ratio
        aspect_ratio = w / h if h > 0 else 0
        if not (human_min_aspect < aspect_ratio < human_max_aspect):
            return False, f"Aspect ratio {aspect_ratio:.2f} out of range"

        # Check shape properties
        perimeter = cv2.arcLength(contour, True)
        if perimeter > 0:
            circularity = 4 * math.pi * area / (perimeter * perimeter)
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            solidity = area / hull_area if hull_area > 0 else 0

            # Human-like properties
            if circularity < 0.8 and solidity > 0.7:
                confidence = min(1.0, (area / human_max_area) * 0.8 + solidity * 0.2)
                return True, f"Human detected (confidence: {confidence:.2f})"

        return False, "Shape analysis failed"

    # Test with synthetic contours
    print("Testing with synthetic contours:")

    # Test 1: Valid human-like contour
    test_contour_1 = np.array([[[100, 100]], [[100, 200]], [[150, 200]], [[150, 100]]], dtype=np.int32)
    is_human, message = analyze_contour_for_human(test_contour_1)
    print(f"  Test 1 (rectangle): {message}")

    # Test 2: Too small
    test_contour_2 = np.array([[[0, 0]], [[0, 10]], [[10, 10]], [[10, 0]]], dtype=np.int32)
    is_human, message = analyze_contour_for_human(test_contour_2)
    print(f"  Test 2 (small): {message}")

    # Test 3: Wrong aspect ratio (too wide)
    test_contour_3 = np.array([[[0, 0]], [[0, 50]], [[200, 50]], [[200, 0]]], dtype=np.int32)
    is_human, message = analyze_contour_for_human(test_contour_3)
    print(f"  Test 3 (wide): {message}")

    print()
    print("✅ Human detection algorithm test completed!")
    print("The system uses contour analysis to detect human-like shapes.")
    print("This provides a LIDAR-like approach for human figure detection.")

if __name__ == "__main__":
    test_human_detection()
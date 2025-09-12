try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
    print("MediaPipe loaded successfully")
except ImportError as e:
    mp = None
    MEDIAPIPE_AVAILABLE = False
    print(f"MediaPipe not available - using OpenCV fallback mode: {e}")

import cv2
import numpy as np
import logging
import time
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class MediaPipeProcessor:
    def __init__(self):
        """Initialize MediaPipe processors"""
        if not MEDIAPIPE_AVAILABLE:
            self.available = False
            self.pose = None
            self.hands = None
            logger.warning("MediaPipe not available - using OpenCV fallback")
            return
        
        if MEDIAPIPE_AVAILABLE:
            try:
                self.mp_pose = mp.solutions.pose
                self.mp_hands = mp.solutions.hands
                self.mp_drawing = mp.solutions.drawing_utils
                self.mp_drawing_styles = mp.solutions.drawing_styles

                # Initialize pose detector
                self.pose = self.mp_pose.Pose(
                    static_image_mode=False,
                    model_complexity=1,
                    smooth_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )

                # Initialize hands detector
                self.hands = self.mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=2,
                    model_complexity=1,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )

                self.available = True
                logger.info("MediaPipe processor initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize MediaPipe: {e}")
                self.available = False
                self.pose = None
                self.hands = None
        else:
            # Fallback to OpenCV-only mode
            self.available = False
            self.pose = None
            self.hands = None
            logger.info("Using OpenCV fallback mode - MediaPipe not available")

    def is_available(self) -> bool:
        """Check if MediaPipe is available"""
        return self.available

    def get_timestamp(self) -> float:
        """Get current timestamp"""
        return time.time()

    def process_pose(self, frame: np.ndarray) -> Dict[str, Any]:
        """Process pose detection on a frame"""
        if not self.available or self.pose is None:
            return {
                "detected": False,
                "error": "MediaPipe not available",
                "landmarks": [],
                "bbox": None,
                "confidence": 0.0
            }

        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Process with MediaPipe
            results = self.pose.process(rgb_frame)

            pose_data = {
                "detected": results.pose_landmarks is not None,
                "landmarks": [],
                "bbox": None,
                "confidence": 0.0
            }

            if results.pose_landmarks:
                # Extract landmarks
                height, width = frame.shape[:2]
                landmarks = []

                for landmark in results.pose_landmarks.landmark:
                    landmarks.append({
                        "x": landmark.x,
                        "y": landmark.y,
                        "z": landmark.z,
                        "visibility": landmark.visibility
                    })

                pose_data["landmarks"] = landmarks

                # Calculate bounding box
                x_coords = [lm["x"] for lm in landmarks]
                y_coords = [lm["y"] for lm in landmarks]

                if x_coords and y_coords:
                    min_x = min(x_coords)
                    max_x = max(x_coords)
                    min_y = min(y_coords)
                    max_y = max(y_coords)

                    pose_data["bbox"] = {
                        "x": int(min_x * width),
                        "y": int(min_y * height),
                        "width": int((max_x - min_x) * width),
                        "height": int((max_y - min_y) * height)
                    }

                # Calculate average confidence
                avg_visibility = np.mean([lm["visibility"] for lm in landmarks])
                pose_data["confidence"] = float(avg_visibility)

            return pose_data

        except Exception as e:
            logger.error(f"Pose processing error: {e}")
            return {
                "detected": False,
                "error": str(e),
                "landmarks": [],
                "bbox": None,
                "confidence": 0.0
            }

    def process_hands(self, frame: np.ndarray) -> Dict[str, Any]:
        """Process hand detection on a frame"""
        if not self.available or self.hands is None:
            return {
                "detected": False,
                "error": "MediaPipe not available",
                "hands": [],
                "hand_count": 0
            }

        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Process with MediaPipe
            results = self.hands.process(rgb_frame)

            hands_data = {
                "detected": results.multi_hand_landmarks is not None,
                "hands": [],
                "hand_count": 0
            }

            if results.multi_hand_landmarks:
                height, width = frame.shape[:2]
                hands = []

                for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    hand_data = {
                        "index": hand_idx,
                        "landmarks": [],
                        "bbox": None,
                        "handedness": "unknown"
                    }

                    # Extract landmarks
                    landmarks = []
                    for landmark in hand_landmarks.landmark:
                        landmarks.append({
                            "x": landmark.x,
                            "y": landmark.y,
                            "z": landmark.z
                        })

                    hand_data["landmarks"] = landmarks

                    # Calculate bounding box
                    x_coords = [lm["x"] for lm in landmarks]
                    y_coords = [lm["y"] for lm in landmarks]

                    if x_coords and y_coords:
                        min_x = min(x_coords)
                        max_x = max(x_coords)
                        min_y = min(y_coords)
                        max_y = max(y_coords)

                        hand_data["bbox"] = {
                            "x": int(min_x * width),
                            "y": int(min_y * height),
                            "width": int((max_x - min_x) * width),
                            "height": int((max_y - min_y) * height)
                        }

                    # Determine handedness if available
                    if results.multi_handedness:
                        handedness = results.multi_handedness[hand_idx]
                        hand_data["handedness"] = handedness.classification[0].label.lower()

                    hands.append(hand_data)

                hands_data["hands"] = hands
                hands_data["hand_count"] = len(hands)

            return hands_data

        except Exception as e:
            logger.error(f"Hand processing error: {e}")
            return {
                "detected": False,
                "error": str(e),
                "hands": [],
                "hand_count": 0
            }

    def process_combined(self, frame: np.ndarray) -> Dict[str, Any]:
        """Process both pose and hands detection"""
        pose_result = self.process_pose(frame)
        hands_result = self.process_hands(frame)

        return {
            "pose": pose_result,
            "hands": hands_result,
            "timestamp": self.get_timestamp()
        }

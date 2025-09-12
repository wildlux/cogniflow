import httpx
import asyncio
from typing import Optional, Dict, Any, List
import logging
import cv2
import numpy as np
import time

class MediaPipeClient:
    def __init__(self, service_url: str = "http://localhost:8001"):
        self.service_url = service_url
        self.client = httpx.AsyncClient(timeout=5.0)
        self.logger = logging.getLogger(__name__)
        self.available = True
        self.last_health_check = 0
        self.health_check_interval = 30  # seconds

    async def check_health(self) -> bool:
        """Check if MediaPipe service is available"""
        current_time = time.time()
        if current_time - self.last_health_check < self.health_check_interval:
            return self.available

        try:
            response = await self.client.get(f"{self.service_url}/health")
            self.available = response.status_code == 200
            self.last_health_check = current_time

            if self.available:
                data = response.json()
                self.logger.info(f"MediaPipe service healthy: {data}")
            else:
                self.logger.warning("MediaPipe service health check failed")

        except Exception as e:
            self.logger.warning(f"MediaPipe service health check error: {e}")
            self.available = False

        return self.available

    async def detect_pose(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """Detect human pose using MediaPipe service"""
        if not await self.check_health():
            return None

        try:
            # Convert frame to JPEG bytes
            success, buffer = cv2.imencode('.jpg', frame)
            if not success:
                self.logger.error("Failed to encode frame to JPEG")
                return None

            frame_bytes = buffer.tobytes()

            # Send to MediaPipe service
            response = await self.client.post(
                f"{self.service_url}/detect_pose",
                files={"file": ("frame.jpg", frame_bytes, "image/jpeg")}
            )

            if response.status_code == 200:
                result = response.json()
                self.logger.debug(f"Pose detection result: detected={result.get('detected', False)}")
                return result
            else:
                self.logger.warning(f"MediaPipe pose detection failed: {response.status_code}")
                self.available = False
                return None

        except Exception as e:
            self.logger.error(f"Pose detection error: {e}")
            self.available = False
            return None

    async def detect_hands(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """Detect hands using MediaPipe service"""
        if not await self.check_health():
            return None

        try:
            # Convert frame to JPEG bytes
            success, buffer = cv2.imencode('.jpg', frame)
            if not success:
                self.logger.error("Failed to encode frame to JPEG")
                return None

            frame_bytes = buffer.tobytes()

            # Send to MediaPipe service
            response = await self.client.post(
                f"{self.service_url}/detect_hands",
                files={"file": ("frame.jpg", frame_bytes, "image/jpeg")}
            )

            if response.status_code == 200:
                result = response.json()
                self.logger.debug(f"Hand detection result: detected={result.get('detected', False)}")
                return result
            else:
                self.logger.warning(f"MediaPipe hand detection failed: {response.status_code}")
                self.available = False
                return None

        except Exception as e:
            self.logger.error(f"Hand detection error: {e}")
            self.available = False
            return None

    async def detect_combined(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """Detect both pose and hands using MediaPipe service"""
        if not await self.check_health():
            return None

        try:
            # Convert frame to JPEG bytes
            success, buffer = cv2.imencode('.jpg', frame)
            if not success:
                self.logger.error("Failed to encode frame to JPEG")
                return None

            frame_bytes = buffer.tobytes()

            # Send to MediaPipe service
            response = await self.client.post(
                f"{self.service_url}/detect_combined",
                files={"file": ("frame.jpg", frame_bytes, "image/jpeg")}
            )

            if response.status_code == 200:
                result = response.json()
                return result
            else:
                self.logger.warning(f"MediaPipe combined detection failed: {response.status_code}")
                self.available = False
                return None

        except Exception as e:
            self.logger.error(f"Combined detection error: {e}")
            self.available = False
            return None

    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status"""
        return {
            "available": self.available,
            "service_url": self.service_url,
            "last_health_check": self.last_health_check
        }

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
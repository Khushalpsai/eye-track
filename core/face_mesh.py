"""
GazeBoard V2 — FaceMesh Detector (Asynchronous Multi-Threaded AI Pipeline)
Wraps MediaPipe FaceLandmarker with background worker thread execution for
maximum FPS and butter-smooth rendering.
"""

from __future__ import annotations

import os
import threading
import time
import urllib.request
from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from utils.landmarks import LEFT_EYE, LEFT_IRIS, RIGHT_EYE, RIGHT_IRIS

Point2D = Tuple[float, float]
Point3D = Tuple[float, float, float]

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
MODEL_PATH = "face_landmarker.task"


@dataclass
class FaceMeshResult:
    """Container for a single frame's face-mesh output."""

    landmarks: List[Point3D]
    left_eye: List[Point2D]
    right_eye: List[Point2D]
    left_iris_center: Point2D
    right_iris_center: Point2D
    all_landmarks_px: List[Point2D]


class FaceMeshDetector:
    """Detects a single face and extracts eye / iris landmarks via MediaPipe 1.0 Tasks API."""

    def __init__(self, model_path: str = MODEL_PATH) -> None:
        """Initialise the MediaPipe FaceLandmarker task."""
        if not os.path.exists(model_path):
            print(f"[FaceMesh] Downloading model from {MODEL_URL}...")
            urllib.request.urlretrieve(MODEL_URL, model_path)

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            num_faces=1,
        )
        self._landmarker = vision.FaceLandmarker.create_from_options(options)

        # Multi-threading state for Async inference
        self._latest_frame: Optional[np.ndarray] = None
        self._latest_result: Optional[FaceMeshResult] = None
        self._lock = threading.Lock()
        self._running = True
        self._new_frame_event = threading.Event()

        # Dedicated background worker thread for AI processing
        self._worker_thread = threading.Thread(target=self._ai_worker_loop, daemon=True)
        self._worker_thread.start()

    def submit_frame(self, frame: np.ndarray) -> None:
        """Submit a new frame for background AI processing (non-blocking)."""
        with self._lock:
            self._latest_frame = frame.copy()
        self._new_frame_event.set()

    def get_latest_result(self) -> Optional[FaceMeshResult]:
        """Get the latest completed AI tracking result instantly (0ms delay)."""
        with self._lock:
            return self._latest_result

    def _ai_worker_loop(self) -> None:
        """Background thread worker that processes AI face landmarker inference."""
        while self._running:
            if self._new_frame_event.wait(timeout=0.001):
                self._new_frame_event.clear()
                with self._lock:
                    frame = self._latest_frame

                if frame is not None:
                    res = self.process(frame)
                    with self._lock:
                        self._latest_result = res
            else:
                time.sleep(0)

    def process(self, frame: np.ndarray) -> Optional[FaceMeshResult]:
        """Synchronous face-mesh inference on an RGB numpy frame (H, W, 3)."""
        h, w = frame.shape[:2]

        if w > 240:
            inference_frame = cv2.resize(frame, (240, 180), interpolation=cv2.INTER_NEAREST)
        else:
            inference_frame = frame

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=inference_frame)
        results = self._landmarker.detect(mp_image)

        if not results.face_landmarks:
            return None

        face = results.face_landmarks[0]

        landmarks: List[Point3D] = [(lm.x, lm.y, lm.z) for lm in face]
        all_landmarks_px: List[Point2D] = [(lm.x * w, lm.y * h) for lm in face]

        left_eye: List[Point2D] = [(face[i].x, face[i].y) for i in LEFT_EYE]
        right_eye: List[Point2D] = [(face[i].x, face[i].y) for i in RIGHT_EYE]

        left_iris_center: Point2D = (face[LEFT_IRIS[0]].x, face[LEFT_IRIS[0]].y)
        right_iris_center: Point2D = (face[RIGHT_IRIS[0]].x, face[RIGHT_IRIS[0]].y)

        return FaceMeshResult(
            landmarks=landmarks,
            left_eye=left_eye,
            right_eye=right_eye,
            left_iris_center=left_iris_center,
            right_iris_center=right_iris_center,
            all_landmarks_px=all_landmarks_px,
        )

    def release(self) -> None:
        """Release MediaPipe resources."""
        self._running = False
        if hasattr(self._landmarker, "close"):
            self._landmarker.close()

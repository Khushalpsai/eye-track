"""
GazeBoard V2 — FaceMesh Detector
Wraps MediaPipe FaceMesh to extract eye, iris, and full-face landmarks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import mediapipe as mp
import numpy as np

from utils.landmarks import LEFT_EYE, LEFT_IRIS, RIGHT_EYE, RIGHT_IRIS

# Type aliases for readability
Point2D = Tuple[float, float]
Point3D = Tuple[float, float, float]


@dataclass
class FaceMeshResult:
    """Container for a single frame's face-mesh output.

    Attributes:
        landmarks:          All 478 landmarks as normalised (x, y, z) tuples.
        left_eye:           6 EAR key-points for the left eye as (x, y) normalised.
        right_eye:          6 EAR key-points for the right eye as (x, y) normalised.
        left_iris_center:   Centre of the left iris as (x, y) normalised.
        right_iris_center:  Centre of the right iris as (x, y) normalised.
        all_landmarks_px:   All 478 landmarks as (x, y) pixel coordinates for debug drawing.
    """

    landmarks: List[Point3D]
    left_eye: List[Point2D]
    right_eye: List[Point2D]
    left_iris_center: Point2D
    right_iris_center: Point2D
    all_landmarks_px: List[Point2D]


class FaceMeshDetector:
    """Detects a single face and extracts eye / iris landmarks via MediaPipe.

    Usage::

        detector = FaceMeshDetector()
        result = detector.process(rgb_frame)
        if result is not None:
            print(result.left_iris_center)
        detector.release()
    """

    def __init__(self) -> None:
        """Initialise the MediaPipe FaceMesh solution.

        ``refine_landmarks=True`` enables the 10 iris landmarks (468-477).
        """
        self._face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    # ──────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────

    def process(self, frame: np.ndarray) -> Optional[FaceMeshResult]:
        """Run face-mesh inference on an RGB frame.

        Args:
            frame: An RGB ``np.ndarray`` of shape ``(H, W, 3)``.

        Returns:
            A :class:`FaceMeshResult` if a face is found, otherwise ``None``.
        """
        results = self._face_mesh.process(frame)

        if results.multi_face_landmarks is None:
            return None

        face = results.multi_face_landmarks[0]
        h, w = frame.shape[:2]

        # Full landmark list (normalised)
        landmarks: List[Point3D] = [
            (lm.x, lm.y, lm.z) for lm in face.landmark
        ]

        # Pixel-scaled (x, y) for every landmark (debug drawing)
        all_landmarks_px: List[Point2D] = [
            (lm.x * w, lm.y * h) for lm in face.landmark
        ]

        # EAR key-points — normalised (x, y)
        left_eye: List[Point2D] = [
            (face.landmark[i].x, face.landmark[i].y) for i in LEFT_EYE
        ]
        right_eye: List[Point2D] = [
            (face.landmark[i].x, face.landmark[i].y) for i in RIGHT_EYE
        ]

        # Iris centres — use index 0 of each iris group (the centre landmark)
        left_iris_center: Point2D = (
            face.landmark[LEFT_IRIS[0]].x,
            face.landmark[LEFT_IRIS[0]].y,
        )
        right_iris_center: Point2D = (
            face.landmark[RIGHT_IRIS[0]].x,
            face.landmark[RIGHT_IRIS[0]].y,
        )

        return FaceMeshResult(
            landmarks=landmarks,
            left_eye=left_eye,
            right_eye=right_eye,
            left_iris_center=left_iris_center,
            right_iris_center=right_iris_center,
            all_landmarks_px=all_landmarks_px,
        )

    def release(self) -> None:
        """Release the underlying MediaPipe resources."""
        self._face_mesh.close()

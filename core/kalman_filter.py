"""
GazeBoard V2 — 2D Kalman Filter for Gaze Smoothing

Smooths raw gaze coordinates using a constant-velocity Kalman filter.
State vector tracks position and velocity in 2D: [x, y, vx, vy].
"""

import math
from typing import Optional, Tuple

import numpy as np

from config import (
    JITTER_DEADZONE_PX,
    KALMAN_MEASUREMENT_NOISE,
    KALMAN_PROCESS_NOISE,
)


class KalmanFilter2D:
    """A 2D Kalman filter for smoothing noisy gaze estimates."""

    def __init__(
        self,
        process_noise: float = KALMAN_PROCESS_NOISE,
        measurement_noise: float = KALMAN_MEASUREMENT_NOISE,
    ) -> None:
        self._process_noise = process_noise
        self._measurement_noise = measurement_noise
        self._initialized: bool = False
        self._init_matrices()

    def _init_matrices(self) -> None:
        """Set all Kalman matrices to their default values."""
        self._F = np.array(
            [
                [1.0, 0.0, 1.0, 0.0],
                [0.0, 1.0, 0.0, 1.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        )

        self._H = np.array(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
            ],
            dtype=np.float64,
        )

        self._Q = np.eye(4, dtype=np.float64) * self._process_noise
        self._R = np.eye(2, dtype=np.float64) * self._measurement_noise
        self._P = np.eye(4, dtype=np.float64) * 1000.0
        self._x = np.zeros((4, 1), dtype=np.float64)
        self._last_stable_pos: Optional[Tuple[float, float]] = None

    def predict(self) -> None:
        self._x = self._F @ self._x
        self._P = self._F @ self._P @ self._F.T + self._Q

    def update(self, measurement: Tuple[float, float]) -> Tuple[float, float]:
        mx, my = float(measurement[0]), float(measurement[1])
        z = np.array([[mx], [my]], dtype=np.float64)

        if not self._initialized:
            self._x[0, 0] = mx
            self._x[1, 0] = my
            self._initialized = True
            return (mx, my)

        # Predict
        self.predict()

        # Update
        y = z - self._H @ self._x
        S = self._H @ self._P @ self._H.T + self._R
        K = self._P @ self._H.T @ np.linalg.inv(S)
        self._x = self._x + K @ y

        I4 = np.eye(4, dtype=np.float64)
        IKH = I4 - K @ self._H
        self._P = IKH @ self._P @ IKH.T + K @ self._R @ K.T

        current_pos = (float(self._x[0, 0]), float(self._x[1, 0]))
        if self._last_stable_pos is not None:
            dx = current_pos[0] - self._last_stable_pos[0]
            dy = current_pos[1] - self._last_stable_pos[1]
            if (dx * dx + dy * dy) < (JITTER_DEADZONE_PX * JITTER_DEADZONE_PX):
                return self._last_stable_pos

        self._last_stable_pos = current_pos
        return current_pos

    def reset(self) -> None:
        self._initialized = False
        self._init_matrices()

    @property
    def position(self) -> Tuple[float, float]:
        return (float(self._x[0, 0]), float(self._x[1, 0]))

    @property
    def velocity(self) -> Tuple[float, float]:
        return (float(self._x[2, 0]), float(self._x[3, 0]))

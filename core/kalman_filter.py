"""
GazeBoard V2 — 2D Kalman Filter for Gaze Smoothing

Smooths raw gaze coordinates using a constant-velocity Kalman filter.
State vector tracks position and velocity in 2D: [x, y, vx, vy].
"""

import numpy as np
from config import KALMAN_PROCESS_NOISE, KALMAN_MEASUREMENT_NOISE

from typing import Tuple, Optional


class KalmanFilter2D:
    """A 2D Kalman filter for smoothing noisy gaze estimates.

    Uses a constant-velocity motion model to predict gaze position and
    fuses incoming measurements to produce a smooth, low-jitter output.

    State vector (4×1):
        [x, y, vx, vy]  — position and velocity in screen coordinates.

    Measurement vector (2×1):
        [x, y]  — raw gaze position from the gaze estimator.

    Attributes:
        _x: State vector (4×1).
        _P: Error covariance matrix (4×4).
        _F: State transition matrix (4×4).
        _H: Measurement matrix (2×4).
        _Q: Process noise covariance (4×4).
        _R: Measurement noise covariance (2×2).
        _initialized: Whether the filter has received its first measurement.
    """

    def __init__(
        self,
        process_noise: float = KALMAN_PROCESS_NOISE,
        measurement_noise: float = KALMAN_MEASUREMENT_NOISE,
    ) -> None:
        """Initialize the Kalman filter with noise parameters.

        Args:
            process_noise: Diagonal value for the process noise covariance Q.
                Higher values make the filter more responsive but noisier.
            measurement_noise: Diagonal value for the measurement noise
                covariance R.  Higher values make the output smoother but
                introduce more lag.
        """
        self._process_noise = process_noise
        self._measurement_noise = measurement_noise
        self._initialized: bool = False
        self._init_matrices()

    # ── Matrix Initialization ────────────────────────────────────────

    def _init_matrices(self) -> None:
        """Set all Kalman matrices to their default values."""
        # State transition matrix (constant-velocity, dt=1)
        self._F = np.array(
            [
                [1.0, 0.0, 1.0, 0.0],
                [0.0, 1.0, 0.0, 1.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        )

        # Measurement matrix — extracts [x, y] from state
        self._H = np.array(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
            ],
            dtype=np.float64,
        )

        # Process noise covariance
        self._Q = np.eye(4, dtype=np.float64) * self._process_noise

        # Measurement noise covariance
        self._R = np.eye(2, dtype=np.float64) * self._measurement_noise

        # Error covariance — high initial uncertainty
        self._P = np.eye(4, dtype=np.float64) * 1000.0

        # State vector — zeros until first measurement arrives
        self._x = np.zeros((4, 1), dtype=np.float64)

    # ── Core Kalman Steps ────────────────────────────────────────────

    def predict(self) -> None:
        """Run the prediction (time-update) step.

        Projects the current state and covariance forward using the
        constant-velocity motion model:
            x̂⁻ = F · x̂
            P⁻  = F · P · Fᵀ + Q
        """
        self._x = self._F @ self._x
        self._P = self._F @ self._P @ self._F.T + self._Q

    def update(self, measurement: Tuple[float, float]) -> Tuple[float, float]:
        """Incorporate a new gaze measurement and return the smoothed position.

        On the very first call the state is seeded directly from the
        measurement so the cursor doesn't jump from the origin.

        Args:
            measurement: Raw gaze position as an ``(x, y)`` tuple.

        Returns:
            Smoothed ``(x, y)`` position after the Kalman update.
        """
        mx, my = float(measurement[0]), float(measurement[1])
        z = np.array([[mx], [my]], dtype=np.float64)

        # Seed state on first measurement to avoid a large initial jump.
        if not self._initialized:
            self._x[0, 0] = mx
            self._x[1, 0] = my
            # Velocity stays at zero; covariance stays high.
            self._initialized = True
            return (mx, my)

        # --- Predict ---
        self.predict()

        # --- Update (measurement-correction) ---
        # Innovation (measurement residual)
        y = z - self._H @ self._x

        # Innovation covariance
        S = self._H @ self._P @ self._H.T + self._R

        # Kalman gain
        K = self._P @ self._H.T @ np.linalg.inv(S)

        # Updated state estimate
        self._x = self._x + K @ y

        # Updated error covariance (Joseph form for numerical stability)
        I4 = np.eye(4, dtype=np.float64)
        IKH = I4 - K @ self._H
        self._P = IKH @ self._P @ IKH.T + K @ self._R @ K.T

        return self.position

    # ── Convenience ──────────────────────────────────────────────────

    def reset(self) -> None:
        """Reinitialize all matrices to defaults, clearing history."""
        self._initialized = False
        self._init_matrices()

    @property
    def position(self) -> Tuple[float, float]:
        """Current smoothed gaze position ``(x, y)``."""
        return (float(self._x[0, 0]), float(self._x[1, 0]))

    @property
    def velocity(self) -> Tuple[float, float]:
        """Current estimated gaze velocity ``(vx, vy)``."""
        return (float(self._x[2, 0]), float(self._x[3, 0]))

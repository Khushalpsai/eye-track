"""
GazeBoard V2 — Gaze Estimator (Phase 1)

Maps normalized iris positions from MediaPipe to screen-pixel coordinates
using a simple linear mapping.  Webcam x-axis is mirrored, so the mapping
flips x before scaling.  A calibration API is stubbed in for Phase 3.
"""

from __future__ import annotations

from typing import Tuple

from config import SCREEN_WIDTH, SCREEN_HEIGHT


class GazeEstimator:
    """Convert averaged iris centres (normalised 0-1) to screen pixels.

    Phase 1 uses a direct linear mapping with optional calibration offsets
    and scale factors that default to identity (no change).

    Parameters
    ----------
    screen_width : int
        Horizontal screen resolution in pixels.
    screen_height : int
        Vertical screen resolution in pixels.
    """

    def __init__(
        self,
        screen_width: int = SCREEN_WIDTH,
        screen_height: int = SCREEN_HEIGHT,
    ) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Calibration parameters (Phase 3 placeholders)
        self._offset_x: float = 0.0
        self._offset_y: float = 0.0
        self._scale_x: float = 1.0
        self._scale_y: float = 1.0

        # Cached gaze results
        self._raw_gaze: Tuple[float, float] = (0.0, 0.0)
        self._calibrated_gaze: Tuple[float, float] = (0.0, 0.0)

    # ── Core estimation ───────────────────────────────────────

    def estimate(
        self,
        left_iris_center: Tuple[float, float],
        right_iris_center: Tuple[float, float],
    ) -> Tuple[float, float]:
        """Map left/right iris centres to a single screen coordinate.

        Parameters
        ----------
        left_iris_center : tuple[float, float]
            Normalised (x, y) of the left-eye iris centre (0.0–1.0).
        right_iris_center : tuple[float, float]
            Normalised (x, y) of the right-eye iris centre (0.0–1.0).

        Returns
        -------
        tuple[float, float]
            (screen_x, screen_y) clamped to screen bounds.
        """
        # Average both eyes for a combined gaze point
        iris_x = (left_iris_center[0] + right_iris_center[0]) / 2.0
        iris_y = (left_iris_center[1] + right_iris_center[1]) / 2.0

        # Linear mapping — flip x because the webcam image is mirrored
        raw_x = (1.0 - iris_x) * self.screen_width
        raw_y = iris_y * self.screen_height

        self._raw_gaze = (raw_x, raw_y)

        # Apply calibration adjustments
        cal_x = raw_x * self._scale_x + self._offset_x
        cal_y = raw_y * self._scale_y + self._offset_y

        # Clamp to screen bounds
        cal_x = max(0.0, min(cal_x, float(self.screen_width)))
        cal_y = max(0.0, min(cal_y, float(self.screen_height)))

        self._calibrated_gaze = (cal_x, cal_y)
        return self._calibrated_gaze

    # ── Calibration ───────────────────────────────────────────

    def update_calibration(
        self,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
    ) -> None:
        """Store calibration offsets and scale factors for Phase 3.

        Parameters
        ----------
        offset_x : float
            Horizontal pixel offset applied after scaling.
        offset_y : float
            Vertical pixel offset applied after scaling.
        scale_x : float
            Horizontal scale factor (1.0 = identity).
        scale_y : float
            Vertical scale factor (1.0 = identity).
        """
        self._offset_x = offset_x
        self._offset_y = offset_y
        self._scale_x = scale_x
        self._scale_y = scale_y

    # ── Properties ────────────────────────────────────────────

    @property
    def raw_gaze(self) -> Tuple[float, float]:
        """Return the most recent gaze point *before* calibration."""
        return self._raw_gaze

    @property
    def calibrated_gaze(self) -> Tuple[float, float]:
        """Return the most recent gaze point *after* calibration."""
        return self._calibrated_gaze

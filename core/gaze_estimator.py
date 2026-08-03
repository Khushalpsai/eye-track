"""
GazeBoard V2 — Gaze Estimator

Maps normalized iris positions from MediaPipe to screen-pixel coordinates
using a direct linear mapping.
"""

from __future__ import annotations

from typing import Tuple

from config import SCREEN_WIDTH, SCREEN_HEIGHT


class GazeEstimator:
    """Convert averaged iris centres (normalised 0-1) to screen pixels."""

    def __init__(
        self,
        screen_width: int = SCREEN_WIDTH,
        screen_height: int = SCREEN_HEIGHT,
    ) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height

        self._offset_x: float = 0.0
        self._offset_y: float = 0.0
        self._scale_x: float = 1.0
        self._scale_y: float = 1.0

        self._raw_gaze: Tuple[float, float] = (0.0, 0.0)
        self._calibrated_gaze: Tuple[float, float] = (0.0, 0.0)

    def estimate(
        self,
        left_iris_center: Tuple[float, float],
        right_iris_center: Tuple[float, float],
    ) -> Tuple[float, float]:
        """Map left/right iris centres to a single screen coordinate."""
        iris_x = (left_iris_center[0] + right_iris_center[0]) / 2.0
        iris_y = (left_iris_center[1] + right_iris_center[1]) / 2.0

        raw_x = (1.0 - iris_x) * self.screen_width
        raw_y = iris_y * self.screen_height

        self._raw_gaze = (raw_x, raw_y)

        cal_x = raw_x * self._scale_x + self._offset_x
        cal_y = raw_y * self._scale_y + self._offset_y

        cal_x = max(0.0, min(cal_x, float(self.screen_width)))
        cal_y = max(0.0, min(cal_y, float(self.screen_height)))

        self._calibrated_gaze = (cal_x, cal_y)
        return self._calibrated_gaze

    def update_calibration(
        self,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
    ) -> None:
        self._offset_x = offset_x
        self._offset_y = offset_y
        self._scale_x = scale_x
        self._scale_y = scale_y

    @property
    def raw_gaze(self) -> Tuple[float, float]:
        return self._raw_gaze

    @property
    def calibrated_gaze(self) -> Tuple[float, float]:
        return self._calibrated_gaze

"""
GazeBoard V2 — Implicit / Self-Healing Nudge Calibration Engine

Learns spatial offset maps implicitly in the background from successful key selections,
eliminating the need for manual recalibration while adjusting for head posture shifts over time.
"""

from typing import Dict, List, Tuple
import math
import numpy as np

from config import SCREEN_WIDTH, SCREEN_HEIGHT


class NudgeCalibrationEngine:
    """Implicit learning engine that nudges spatial calibration grids on key selections."""

    def __init__(self, screen_w: int = SCREEN_WIDTH, screen_h: int = SCREEN_HEIGHT) -> None:
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.learning_rate: float = 0.15

        # 4 Quadrant Offsets: [Top-Left, Top-Right, Bottom-Left, Bottom-Right]
        # Each entry is [offset_x, offset_y]
        self._quad_offsets: Dict[str, np.ndarray] = {
            "TL": np.array([0.0, 0.0], dtype=np.float64),
            "TR": np.array([0.0, 0.0], dtype=np.float64),
            "BL": np.array([0.0, 0.0], dtype=np.float64),
            "BR": np.array([0.0, 0.0], dtype=np.float64),
        }

        # History log for RMS confidence score calculation (last 20 selections)
        self._error_history: List[float] = []
        self.total_selections: int = 0

    def register_success(
        self, gaze_point: Tuple[float, float], target_center: Tuple[float, float]
    ) -> None:
        """Log a successful key selection and nudge the spatial offset map.

        Parameters
        ----------
        gaze_point : Tuple[float, float]
            The (x, y) gaze point when selection fired.
        target_center : Tuple[float, float]
            The exact (x, y) center of the selected key.
        """
        gx, gy = gaze_point
        tx, ty = target_center

        # Error vector (how far the gaze was from key center)
        err_x = tx - gx
        err_y = ty - gy
        dist = math.hypot(err_x, err_y)

        # Track error history (keep last 20)
        self._error_history.append(dist)
        if len(self._error_history) > 20:
            self._error_history.pop(0)
        self.total_selections += 1

        # Determine target quadrant
        quad_id = self._get_quadrant_id(tx, ty)

        # Apply Nudge learning update: Offset_new = Offset_old + rate * Error
        nudge = np.array([err_x, err_y], dtype=np.float64) * self.learning_rate
        self._quad_offsets[quad_id] += nudge

        print(
            f"[Nudge Engine] Selected key center ({tx:.0f}, {ty:.0f}). "
            f"Quadrant {quad_id} nudged by ({nudge[0]:.1f}, {nudge[1]:.1f})px. Error: {dist:.1f}px"
        )

    def get_offset(self, x: float, y: float) -> Tuple[float, float]:
        """Compute smooth spatial bilinear offset for any (x, y) gaze point."""
        u = max(0.0, min(1.0, x / self.screen_w))
        v = max(0.0, min(1.0, y / self.screen_h))

        # Bilinear interpolation between the 4 quadrant offsets
        tl = self._quad_offsets["TL"]
        tr = self._quad_offsets["TR"]
        bl = self._quad_offsets["BL"]
        br = self._quad_offsets["BR"]

        top = (1.0 - u) * tl + u * tr
        bottom = (1.0 - u) * bl + u * br
        offset = (1.0 - v) * top + v * bottom

        return (float(offset[0]), float(offset[1]))

    def _get_quadrant_id(self, x: float, y: float) -> str:
        mid_x = self.screen_w / 2.0
        mid_y = self.screen_h / 2.0
        if x < mid_x:
            return "TL" if y < mid_y else "BL"
        else:
            return "TR" if y < mid_y else "BR"

    def seed_offsets(self, initial_offsets: Dict[str, Tuple[float, float]]) -> None:
        """Seed initial quadrant offsets from the 4-Point Bootstrapper."""
        for q_id, off in initial_offsets.items():
            if q_id in self._quad_offsets:
                self._quad_offsets[q_id] = np.array([off[0], off[1]], dtype=np.float64)

    @property
    def confidence_score(self) -> float:
        """Return calibration confidence percentage (0-100%) based on recent RMS error."""
        if not self._error_history:
            return 50.0  # Default baseline
        rms = math.sqrt(sum(e * e for e in self._error_history) / len(self._error_history))
        # 0px error = 100%, 150px error = 0%
        score = max(0.0, min(100.0, 100.0 - (rms / 1.5)))
        return score

    def reset(self) -> None:
        """Reset offsets and error history."""
        for q_id in self._quad_offsets:
            self._quad_offsets[q_id] = np.array([0.0, 0.0], dtype=np.float64)
        self._error_history.clear()
        self.total_selections = 0

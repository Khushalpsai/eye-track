"""
GazeBoard V2 — Blink Detector

EAR (Eye Aspect Ratio) based blink detection with classification
into NATURAL, LONG, and DOUBLE blink types.
"""

import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Tuple

import numpy as np

from config import (
    DOUBLE_BLINK_WINDOW_MS,
    EAR_THRESHOLD,
    LONG_BLINK_MAX_MS,
    LONG_BLINK_MIN_MS,
    NATURAL_BLINK_MAX_MS,
    NATURAL_BLINK_MIN_MS,
)


class BlinkType(Enum):
    """Types of intentional blink events."""

    NATURAL = auto()
    LONG = auto()
    DOUBLE = auto()


@dataclass
class BlinkEvent:
    """Represents a detected blink event.

    Attributes:
        blink_type: The classified type of the blink.
        duration_ms: How long the eyes were closed, in milliseconds.
    """

    blink_type: BlinkType
    duration_ms: float


class _EyeState(Enum):
    """Internal eye state tracker."""

    OPEN = auto()
    CLOSING = auto()


class BlinkDetector:
    """Detects and classifies blinks using the Eye Aspect Ratio (EAR).

    The detector tracks eye open/close state transitions and classifies
    blinks by their duration:
      - **NATURAL**: A normal involuntary blink (80–300 ms).
      - **LONG**: An intentional sustained closure (500–2000 ms).
      - **DOUBLE**: Two consecutive NATURAL blinks within 500 ms.

    Blinks that are too short (< 80 ms, likely noise) or too long
    (> 2000 ms, likely resting) are silently discarded.

    Args:
        ear_threshold: EAR value below which eyes are considered closed.
        natural_blink_min_ms: Minimum duration for a natural blink.
        natural_blink_max_ms: Maximum duration for a natural blink.
        long_blink_min_ms: Minimum duration for a long blink.
        long_blink_max_ms: Maximum duration for a long blink.
        double_blink_window_ms: Max gap between two natural blinks to
            register as a double blink.
    """

    def __init__(
        self,
        ear_threshold: float = EAR_THRESHOLD,
        natural_blink_min_ms: float = NATURAL_BLINK_MIN_MS,
        natural_blink_max_ms: float = NATURAL_BLINK_MAX_MS,
        long_blink_min_ms: float = LONG_BLINK_MIN_MS,
        long_blink_max_ms: float = LONG_BLINK_MAX_MS,
        double_blink_window_ms: float = DOUBLE_BLINK_WINDOW_MS,
    ) -> None:
        # Thresholds
        self._ear_threshold = ear_threshold
        self._natural_min = natural_blink_min_ms
        self._natural_max = natural_blink_max_ms
        self._long_min = long_blink_min_ms
        self._long_max = long_blink_max_ms
        self._double_window = double_blink_window_ms

        # Runtime state
        self._state = _EyeState.OPEN
        self._close_start: float = 0.0  # timestamp when eyes closed
        self._current_ear: float = 0.0
        self._last_natural_blink_time: float = 0.0  # for double-blink detection

    # ── Static helpers ────────────────────────────────────

    @staticmethod
    def calculate_ear(eye_points: List[Tuple[float, float]]) -> float:
        """Compute the Eye Aspect Ratio for a single eye.

        EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)

        A higher EAR indicates an open eye; a value near zero indicates
        a closed eye.

        Args:
            eye_points: Six landmark coordinates ordered as
                [p1, p2, p3, p4, p5, p6] where p1–p4 span the
                horizontal axis and p2/p6, p3/p5 span the vertical axis.

        Returns:
            The eye aspect ratio (float ≥ 0).
        """
        pts = np.array(eye_points, dtype=np.float64)

        # Vertical distances
        v1 = np.linalg.norm(pts[1] - pts[5])  # ||p2 - p6||
        v2 = np.linalg.norm(pts[2] - pts[4])  # ||p3 - p5||

        # Horizontal distance
        h = np.linalg.norm(pts[0] - pts[3])  # ||p1 - p4||

        if h == 0.0:
            return 0.0

        return (v1 + v2) / (2.0 * h)

    # ── Main update loop ──────────────────────────────────

    def update(
        self,
        left_eye: List[Tuple[float, float]],
        right_eye: List[Tuple[float, float]],
    ) -> Optional[BlinkEvent]:
        """Process a new frame and return a blink event if one completed.

        Call this once per frame with the six eye landmarks for each eye.

        Args:
            left_eye: Six (x, y) landmarks for the left eye.
            right_eye: Six (x, y) landmarks for the right eye.

        Returns:
            A :class:`BlinkEvent` when a blink has just ended and passes
            classification, or ``None`` otherwise.
        """
        left_ear = self.calculate_ear(left_eye)
        right_ear = self.calculate_ear(right_eye)
        avg_ear = (left_ear + right_ear) / 2.0
        self._current_ear = avg_ear

        now = time.time()

        if self._state == _EyeState.OPEN:
            if avg_ear < self._ear_threshold:
                # Eyes just closed
                self._state = _EyeState.CLOSING
                self._close_start = now
            return None

        # State is CLOSING — eyes are currently shut
        if avg_ear >= self._ear_threshold:
            # Eyes just opened — classify the blink
            self._state = _EyeState.OPEN
            duration_ms = (now - self._close_start) * 1000.0
            return self._classify(duration_ms, now)

        return None

    # ── Classification ────────────────────────────────────

    def _classify(self, duration_ms: float, now: float) -> Optional[BlinkEvent]:
        """Classify a completed blink by its duration.

        Also handles double-blink detection by tracking the time
        between consecutive natural blinks.

        Args:
            duration_ms: Duration the eyes were closed, in milliseconds.
            now: Current timestamp (seconds since epoch).

        Returns:
            A :class:`BlinkEvent` or ``None`` if the blink is noise/rest.
        """
        # Too short — noise / partial detection
        if duration_ms < self._natural_min:
            return None

        # Natural blink range
        if duration_ms <= self._natural_max:
            gap_ms = (now - self._last_natural_blink_time) * 1000.0
            self._last_natural_blink_time = now

            if gap_ms <= self._double_window:
                # Second natural blink arrived fast enough → double
                # Reset so a third blink doesn't chain into another double
                self._last_natural_blink_time = 0.0
                return BlinkEvent(
                    blink_type=BlinkType.DOUBLE, duration_ms=duration_ms
                )

            return BlinkEvent(
                blink_type=BlinkType.NATURAL, duration_ms=duration_ms
            )

        # Gap between natural and long range — ignore
        if duration_ms < self._long_min:
            return None

        # Long (intentional) blink range
        if duration_ms <= self._long_max:
            return BlinkEvent(
                blink_type=BlinkType.LONG, duration_ms=duration_ms
            )

        # Too long — user is resting / away
        return None

    # ── Properties ────────────────────────────────────────

    @property
    def current_ear(self) -> float:
        """Latest averaged EAR value across both eyes."""
        return self._current_ear

    @property
    def is_eyes_closed(self) -> bool:
        """``True`` when the EAR is currently below the threshold."""
        return self._state == _EyeState.CLOSING

    @property
    def eyes_closed_duration_ms(self) -> float:
        """Milliseconds the eyes have been continuously closed.

        Returns 0.0 when the eyes are open.
        """
        if self._state == _EyeState.OPEN:
            return 0.0
        return (time.time() - self._close_start) * 1000.0

"""
GazeBoard V2 — Dwell Selection Engine
Tracks gaze focus across UI key bounding boxes, computes animated radial
fill progress (0.0 to 1.0), and manages re-dwell cooldowns.
"""

import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import pygame

from config import DWELL_TIME_MS, RE_DWELL_COOLDOWN_MS


@dataclass
class SelectionResult:
    """Telemetry output from the selection engine per frame.

    Attributes:
        active_key_id: ID of the key currently being focused (or None).
        dwell_progress: Progress from 0.0 to 1.0 (for drawing radial ring).
        triggered_key_id: ID of the key that passed 100% or long blink (or None).
    """

    active_key_id: Optional[str]
    dwell_progress: float
    triggered_key_id: Optional[str]


class SelectionEngine:
    """Tracks gaze hover over interactive UI elements and handles dwell activation."""

    def __init__(
        self,
        dwell_time_ms: float = DWELL_TIME_MS,
        cooldown_ms: float = RE_DWELL_COOLDOWN_MS,
    ) -> None:
        self.dwell_time_ms = dwell_time_ms
        self.cooldown_ms = cooldown_ms

        self._active_key_id: Optional[str] = None
        self._focus_start_time: float = 0.0
        self._last_trigger_key_id: Optional[str] = None
        self._last_trigger_time: float = 0.0

    def update(
        self,
        gaze_point: Tuple[float, float],
        is_long_blink: bool,
        key_rects: Dict[str, pygame.Rect],
    ) -> SelectionResult:
        """Update selection state based on current gaze point and key bounding boxes.

        Parameters
        ----------
        gaze_point : Tuple[float, float]
            Smoothed (x, y) gaze pixel coordinates.
        is_long_blink : bool
            True if a long blink event was detected in this frame.
        key_rects : Dict[str, pygame.Rect]
            Map of key identifiers to their Pygame screen bounding rects.

        Returns
        -------
        SelectionResult
            Container with active key ID, dwell progress (0.0-1.0), and triggered key ID.
        """
        now = time.time()
        now_ms = now * 1000.0
        gx, gy = gaze_point

        # 1. Identify which key bounding box contains the gaze point
        hovered_key_id: Optional[str] = None
        for key_id, rect in key_rects.items():
            if rect.collidepoint(gx, gy):
                hovered_key_id = key_id
                break

        # 2. Check re-dwell cooldown (prevent immediate re-triggering of same key)
        if (
            hovered_key_id == self._last_trigger_key_id
            and (now_ms - self._last_trigger_time) < self.cooldown_ms
        ):
            return SelectionResult(
                active_key_id=hovered_key_id,
                dwell_progress=0.0,
                triggered_key_id=None,
            )

        # 3. Handle key focus transitions
        if hovered_key_id != self._active_key_id:
            self._active_key_id = hovered_key_id
            self._focus_start_time = now_ms

        if self._active_key_id is None:
            return SelectionResult(
                active_key_id=None,
                dwell_progress=0.0,
                triggered_key_id=None,
            )

        # 4. Long Blink Instant Trigger (overrides dwell timer)
        if is_long_blink and self._active_key_id:
            triggered = self._active_key_id
            self._last_trigger_key_id = triggered
            self._last_trigger_time = now_ms
            self._focus_start_time = now_ms  # Reset focus timer
            return SelectionResult(
                active_key_id=triggered,
                dwell_progress=1.0,
                triggered_key_id=triggered,
            )

        # 5. Dwell Time Calculation
        elapsed_ms = now_ms - self._focus_start_time
        progress = min(1.0, max(0.0, elapsed_ms / self.dwell_time_ms))

        # 6. Trigger on 100% Dwell
        if progress >= 1.0:
            triggered = self._active_key_id
            self._last_trigger_key_id = triggered
            self._last_trigger_time = now_ms
            self._focus_start_time = now_ms  # Reset focus timer
            return SelectionResult(
                active_key_id=triggered,
                dwell_progress=1.0,
                triggered_key_id=triggered,
            )

        return SelectionResult(
            active_key_id=self._active_key_id,
            dwell_progress=progress,
            triggered_key_id=None,
        )

    def reset(self) -> None:
        """Reset internal selection state."""
        self._active_key_id = None
        self._focus_start_time = 0.0
        self._last_trigger_key_id = None
        self._last_trigger_time = 0.0

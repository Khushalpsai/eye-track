"""
GazeBoard V2 — Gaze Cursor Renderer

Renders a semi-transparent, pulsing gaze focus point on a Pygame surface.
Color reflects the current tracking state (tracking / low confidence / no face).
"""

import math
import time
from enum import Enum

import pygame

from config import (
    CURSOR_ALPHA,
    CURSOR_COLOR_LOW_CONF,
    CURSOR_COLOR_NO_FACE,
    CURSOR_COLOR_TRACKING,
    CURSOR_PULSE_SPEED,
    CURSOR_RADIUS,
)


class CursorState(Enum):
    """Possible visual states of the gaze cursor."""

    TRACKING = "tracking"
    LOW_CONFIDENCE = "low_confidence"
    NO_FACE = "no_face"


# Convenient lookup so callers can pass plain strings.
_STATE_MAP = {s.value: s for s in CursorState}


class GazeCursor:
    """Renders a gaze focus point with pulsing animation and outer glow.

    Parameters
    ----------
    radius : int
        Base radius of the cursor circle.
    tracking_color : tuple[int, int, int]
        RGB colour used when actively tracking.
    low_conf_color : tuple[int, int, int]
        RGB colour used when confidence is low.
    no_face_color : tuple[int, int, int]
        RGB colour used when no face is detected.
    alpha : int
        Base opacity for the inner cursor (0-255).
    pulse_speed : float
        Speed multiplier for the pulsing animation.
    """

    def __init__(
        self,
        radius: int = CURSOR_RADIUS,
        tracking_color: tuple = CURSOR_COLOR_TRACKING,
        low_conf_color: tuple = CURSOR_COLOR_LOW_CONF,
        no_face_color: tuple = CURSOR_COLOR_NO_FACE,
        alpha: int = CURSOR_ALPHA,
        pulse_speed: float = CURSOR_PULSE_SPEED,
    ) -> None:
        self.radius = radius
        self.alpha = alpha
        self.pulse_speed = pulse_speed

        # Map each state to its colour.
        self._colors = {
            CursorState.TRACKING: tracking_color,
            CursorState.LOW_CONFIDENCE: low_conf_color,
            CursorState.NO_FACE: no_face_color,
        }

        # Current position and state.
        self._x: float = 0.0
        self._y: float = 0.0
        self._state: CursorState = CursorState.NO_FACE

    # ── public API ──────────────────────────────────────────

    def update(self, x: float, y: float, state: str) -> None:
        """Update cursor position and tracking state.

        Parameters
        ----------
        x : float
            Horizontal screen coordinate.
        y : float
            Vertical screen coordinate.
        state : str
            One of ``'tracking'``, ``'low_confidence'``, ``'no_face'``.
        """
        self._x = x
        self._y = y
        resolved = _STATE_MAP.get(state)
        if resolved is None:
            raise ValueError(
                f"Invalid cursor state '{state}'. "
                f"Expected one of {list(_STATE_MAP.keys())}."
            )
        self._state = resolved

    def draw(self, surface: pygame.Surface) -> None:
        """Render the cursor onto *surface*.

        The cursor is drawn on a temporary SRCALPHA surface so that
        per-pixel alpha blending works correctly.  A pulsing radius
        animation and an outer glow ring give the cursor a polished feel.

        Parameters
        ----------
        surface : pygame.Surface
            Target surface (typically the main screen).
        """
        color = self._colors[self._state]

        # ── pulsing radius ──────────────────────────────────
        pulse = math.sin(time.time() * self.pulse_speed)
        # Oscillate between 0.85× and 1.15× the base radius.
        scale = 1.0 + 0.15 * pulse
        animated_radius = max(1, int(self.radius * scale))

        # The glow ring is a bit larger than the animated cursor.
        glow_radius = animated_radius + max(4, animated_radius // 3)

        # Size the temporary surface to fit the glow ring comfortably.
        surf_size = (glow_radius + 2) * 2
        temp = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)

        centre = (surf_size // 2, surf_size // 2)

        # ── outer glow ring ─────────────────────────────────
        glow_alpha = max(10, self.alpha // 3)
        glow_color = (*color, glow_alpha)
        pygame.draw.circle(temp, glow_color, centre, glow_radius)

        # ── inner filled cursor ─────────────────────────────
        inner_color = (*color, self.alpha)
        pygame.draw.circle(temp, inner_color, centre, animated_radius)

        # Blit the temporary surface centred on (x, y).
        blit_x = int(self._x) - surf_size // 2
        blit_y = int(self._y) - surf_size // 2
        surface.blit(temp, (blit_x, blit_y))

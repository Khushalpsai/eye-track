"""
GazeBoard V2 — Debug Overlay

A toggle-able semi-transparent debug panel rendered on the Pygame surface.
Displays real-time telemetry: FPS, EAR values, gaze coordinates,
blink state, face detection status, an EAR bar graph, and optional
face landmark dots.
"""

from typing import Dict, List, Optional, Tuple

import pygame

from config import (
    DEBUG_ACCENT_COLOR,
    DEBUG_BG_COLOR,
    DEBUG_FONT_SIZE,
    DEBUG_PANEL_HEIGHT,
    DEBUG_PANEL_WIDTH,
    DEBUG_TEXT_COLOR,
    EAR_THRESHOLD,
)


class DebugOverlay:
    """Toggle-able debug panel rendered in the top-left corner.

    Provides at-a-glance insight into gaze tracking internals:
    labelled metric rows, a visual EAR bar graph, and optional
    face-landmark dot rendering.

    Args:
        panel_width: Width of the debug panel in pixels.
        panel_height: Height of the debug panel in pixels.
        font_size: Font size for debug text.
        bg_color: RGBA background colour of the panel.
        text_color: RGB colour for label text.
        accent_color: RGB colour for value text.
    """

    def __init__(
        self,
        panel_width: int = DEBUG_PANEL_WIDTH,
        panel_height: int = DEBUG_PANEL_HEIGHT,
        font_size: int = DEBUG_FONT_SIZE,
        bg_color: Tuple[int, ...] = DEBUG_BG_COLOR,
        text_color: Tuple[int, ...] = DEBUG_TEXT_COLOR,
        accent_color: Tuple[int, ...] = DEBUG_ACCENT_COLOR,
    ) -> None:
        self._panel_width = panel_width
        self._panel_height = panel_height
        self._font_size = font_size
        self._bg_color = bg_color
        self._text_color = text_color
        self._accent_color = accent_color

        self._visible = False
        self._data: Dict = {}

        # Initialise font — prefer Consolas, fall back to monospace
        pygame.font.init()
        try:
            self._font = pygame.font.SysFont("consolas", self._font_size)
        except Exception:
            self._font = pygame.font.SysFont("monospace", self._font_size)

        # Layout constants
        self._padding = 10
        self._line_height = self._font_size + 4
        self._bar_height = 12
        self._bar_max_width = self._panel_width - 2 * self._padding

    # ── Properties ────────────────────────────────────────

    @property
    def visible(self) -> bool:
        """Whether the overlay is currently shown."""
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        self._visible = value

    # ── Public methods ────────────────────────────────────

    def toggle(self) -> None:
        """Flip overlay visibility on/off."""
        self._visible = not self._visible

    def update(self, data: dict) -> None:
        """Receive a new snapshot of debug telemetry.

        Expected keys (all optional — missing keys are gracefully skipped):
            - ``fps`` *(float)*: Current frames per second.
            - ``ear_left`` *(float)*: Left-eye EAR.
            - ``ear_right`` *(float)*: Right-eye EAR.
            - ``ear_avg`` *(float)*: Averaged EAR across both eyes.
            - ``gaze_raw`` *(Tuple[int, int])*: Raw gaze coordinates.
            - ``gaze_smooth`` *(Tuple[int, int])*: Kalman-smoothed gaze.
            - ``blink_state`` *(str)*: ``'open'`` or ``'closed'``.
            - ``face_detected`` *(bool)*: Whether a face is visible.
            - ``landmarks_px`` *(List[Tuple[int, int]])*: Pixel-space
              face landmarks for wireframe rendering.

        Args:
            data: Dictionary of debug values to display.
        """
        self._data = data

    def draw(self, surface: pygame.Surface) -> None:
        """Render the debug overlay onto *surface* if visible.

        Args:
            surface: The main Pygame display surface.
        """
        if not self._visible:
            return

        # Build a per-frame SRCALPHA surface for semi-transparency
        panel = pygame.Surface(
            (self._panel_width, self._panel_height), pygame.SRCALPHA
        )
        panel.fill(self._bg_color)

        y = self._padding

        # ── Header ────────────────────────────────────────
        y = self._draw_header(panel, y)

        # ── Metric rows ───────────────────────────────────
        y = self._draw_metrics(panel, y)

        # ── EAR bar graph ─────────────────────────────────
        y = self._draw_ear_bar(panel, y)

        # ── Face landmarks ────────────────────────────────
        self._draw_landmarks(panel, y)

        # Blit the finished panel onto the main surface
        surface.blit(panel, (0, 0))

    # ── Private rendering helpers ─────────────────────────

    def _draw_header(self, panel: pygame.Surface, y: int) -> int:
        """Draw the panel title and a separator line.

        Args:
            panel: The overlay surface.
            y: Current vertical cursor position.

        Returns:
            Updated vertical cursor position.
        """
        title_surf = self._font.render(
            "─── DEBUG ───", True, self._accent_color
        )
        panel.blit(title_surf, (self._padding, y))
        y += self._line_height + 2

        # Thin separator
        pygame.draw.line(
            panel,
            self._accent_color,
            (self._padding, y),
            (self._panel_width - self._padding, y),
        )
        y += 6
        return y

    def _draw_metrics(self, panel: pygame.Surface, y: int) -> int:
        """Render labelled rows for each debug metric.

        Args:
            panel: The overlay surface.
            y: Current vertical cursor position.

        Returns:
            Updated vertical cursor position.
        """
        rows: List[Tuple[str, str]] = []

        # FPS
        fps = self._data.get("fps")
        if fps is not None:
            rows.append(("FPS", f"{fps:6.1f}"))

        # Face detected
        face = self._data.get("face_detected")
        if face is not None:
            rows.append(("Face", "YES" if face else " NO"))

        # Blink state
        blink = self._data.get("blink_state")
        if blink is not None:
            rows.append(("Blink", f"{blink:>6s}"))

        # EAR values
        for key, label in [
            ("ear_left", "EAR L"),
            ("ear_right", "EAR R"),
            ("ear_avg", "EAR  "),
        ]:
            val = self._data.get(key)
            if val is not None:
                rows.append((label, f"{val:6.3f}"))

        # Gaze coordinates
        gaze_raw = self._data.get("gaze_raw")
        if gaze_raw is not None:
            rows.append(("Raw  ", f"({gaze_raw[0]:4.0f},{gaze_raw[1]:4.0f})"))

        gaze_smooth = self._data.get("gaze_smooth")
        if gaze_smooth is not None:
            rows.append(
                ("Smooth", f"({gaze_smooth[0]:4.0f},{gaze_smooth[1]:4.0f})")
            )

        # Self-healing Calibration confidence score %
        calib_conf = self._data.get("calib_conf")
        if calib_conf is not None:
            rows.append(("CalibConf", f"{calib_conf:5.1f}%"))

        for label, value_str in rows:
            label_surf = self._font.render(
                f"{label}:", True, self._text_color
            )
            value_surf = self._font.render(value_str, True, self._accent_color)

            panel.blit(label_surf, (self._padding, y))
            # Right-align values
            value_x = self._panel_width - self._padding - value_surf.get_width()
            panel.blit(value_surf, (value_x, y))
            y += self._line_height

        return y

    def _draw_ear_bar(self, panel: pygame.Surface, y: int) -> int:
        """Draw a horizontal bar graph showing EAR level vs threshold.

        The bar fills proportionally to ``ear_avg`` (capped at 0.5).
        A vertical tick marks the ``EAR_THRESHOLD`` position.

        Args:
            panel: The overlay surface.
            y: Current vertical cursor position.

        Returns:
            Updated vertical cursor position.
        """
        ear_avg = self._data.get("ear_avg")
        if ear_avg is None:
            return y

        y += 4  # small gap

        # Label
        bar_label = self._font.render("EAR Bar:", True, self._text_color)
        panel.blit(bar_label, (self._padding, y))
        y += self._line_height

        bar_x = self._padding
        max_ear = 0.5  # EAR values rarely exceed this

        # Background bar outline
        bar_rect = pygame.Rect(
            bar_x, y, self._bar_max_width, self._bar_height
        )
        pygame.draw.rect(panel, self._text_color, bar_rect, 1)

        # Filled portion
        fill_ratio = min(max(ear_avg / max_ear, 0.0), 1.0)
        fill_width = int(fill_ratio * self._bar_max_width)

        # Colour the bar green when above threshold, red when below
        bar_colour = (
            (80, 200, 120) if ear_avg >= EAR_THRESHOLD else (220, 60, 60)
        )
        if fill_width > 0:
            fill_rect = pygame.Rect(bar_x, y, fill_width, self._bar_height)
            pygame.draw.rect(panel, bar_colour, fill_rect)

        # Threshold tick mark
        thresh_x = bar_x + int((EAR_THRESHOLD / max_ear) * self._bar_max_width)
        pygame.draw.line(
            panel,
            (255, 255, 100),  # yellow tick
            (thresh_x, y - 2),
            (thresh_x, y + self._bar_height + 2),
            2,
        )

        y += self._bar_height + 6
        return y

    def _draw_landmarks(self, panel: pygame.Surface, y: int) -> None:
        """Draw small dots for each face landmark inside the panel.

        Landmarks are normalised to fit within the remaining panel space.

        Args:
            panel: The overlay surface.
            y: Current vertical cursor position (top of landmark area).
        """
        landmarks: Optional[List[Tuple[int, int]]] = self._data.get(
            "landmarks_px"
        )
        if not landmarks:
            return

        # Available drawing area inside the panel
        area_x = self._padding
        area_y = y + 2
        area_w = self._panel_width - 2 * self._padding
        area_h = self._panel_height - area_y - self._padding

        if area_w <= 0 or area_h <= 0:
            return

        # Compute bounding box of landmarks for normalisation
        xs = [p[0] for p in landmarks]
        ys = [p[1] for p in landmarks]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        span_x = max_x - min_x or 1
        span_y = max_y - min_y or 1

        # Scale while preserving aspect ratio
        scale = min(area_w / span_x, area_h / span_y)

        # Centre the landmark cluster
        scaled_w = span_x * scale
        scaled_h = span_y * scale
        offset_x = area_x + (area_w - scaled_w) / 2
        offset_y = area_y + (area_h - scaled_h) / 2

        dot_colour = self._accent_color
        dot_radius = 1

        # Subsample landmarks for fast rendering without Pygame draw-call lag
        for px, py in landmarks[::3]:
            nx = int(offset_x + (px - min_x) * scale)
            ny = int(offset_y + (py - min_y) * scale)
            panel.set_at((nx, ny), dot_colour)

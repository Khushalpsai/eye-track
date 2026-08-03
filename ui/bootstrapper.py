"""
GazeBoard V2 — Quick 4-Point Bootstrapper UI
Renders a 5-second initial calibration sequence at the 4 screen corners
to seed spatial offsets before implicit learning takes over.
"""

import math
import time
from typing import Dict, List, Optional, Tuple

import pygame

from config import COLOR_ACCENT, COLOR_BG, COLOR_DWELL_RING, COLOR_TEXT


class QuickBootstrapper:
    """5-Second 4-Corner Calibration Overlay."""

    def __init__(self, screen_w: int, screen_h: int) -> None:
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.active: bool = False

        pygame.font.init()
        try:
            self.font_title = pygame.font.SysFont("segoeui", 28, bold=True)
            self.font_sub = pygame.font.SysFont("segoeui", 20)
        except Exception:
            self.font_title = pygame.font.SysFont("sans-serif", 28, bold=True)
            self.font_sub = pygame.font.SysFont("sans-serif", 20)

        # 4 Corner Target Points (15% and 85% margins)
        self.points_spec: List[Tuple[str, float, float]] = [
            ("TL", 0.15, 0.15),
            ("TR", 0.85, 0.15),
            ("BL", 0.15, 0.85),
            ("BR", 0.85, 0.85),
        ]

        self._current_idx: int = 0
        self._point_start_time: float = 0.0
        self._samples: List[Tuple[float, float]] = []
        self.seeded_offsets: Optional[Dict[str, Tuple[float, float]]] = None

    def start(self) -> None:
        """Start the 5-second calibration sequence."""
        self.active = True
        self._current_idx = 0
        self._point_start_time = time.time()
        self._samples.clear()
        self.seeded_offsets = None
        print("[Bootstrapper] 5-Second Quick Calibration Started...")

    def update(self, gaze_point: Tuple[float, float]) -> Optional[Dict[str, Tuple[float, float]]]:
        """Update calibration progress and return seeded offsets when complete."""
        if not self.active:
            return None

        now = time.time()
        elapsed = now - self._point_start_time

        # Record gaze sample
        self._samples.append(gaze_point)

        # Each point holds for 1.0 second
        if elapsed >= 1.0:
            q_id, rel_x, rel_y = self.points_spec[self._current_idx]
            target_x = rel_x * self.screen_w
            target_y = rel_y * self.screen_h

            # Compute average gaze during the 1 sec hold
            avg_gx = sum(s[0] for s in self._samples) / len(self._samples)
            avg_gy = sum(s[1] for s in self._samples) / len(self._samples)

            # Seed offset for this quadrant
            err_x = target_x - avg_gx
            err_y = target_y - avg_gy

            if self.seeded_offsets is None:
                self.seeded_offsets = {}
            self.seeded_offsets[q_id] = (err_x, err_y)

            # Move to next point
            self._current_idx += 1
            self._point_start_time = now
            self._samples.clear()

            # Sequence Complete!
            if self._current_idx >= len(self.points_spec):
                self.active = False
                print(f"[Bootstrapper] Quick Calibration Complete! Seeded Offsets: {self.seeded_offsets}")
                return self.seeded_offsets

        return None

    def draw(self, surface: pygame.Surface) -> None:
        """Render calibration target dots and progress indicator."""
        if not self.active or self._current_idx >= len(self.points_spec):
            return

        q_id, rel_x, rel_y = self.points_spec[self._current_idx]
        target_x = int(rel_x * self.screen_w)
        target_y = int(rel_y * self.screen_h)

        now = time.time()
        progress = min(1.0, max(0.0, (now - self._point_start_time) / 1.0))

        # Semi-transparent background overlay
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((15, 17, 26, 220))
        surface.blit(overlay, (0, 0))

        # Instruction Text
        title_surf = self.font_title.render("5-SECOND QUICK CALIBRATION", True, COLOR_TEXT)
        sub_surf = self.font_sub.render(
            f"Stare directly at the glowing dot ({self._current_idx + 1}/4)...", True, COLOR_ACCENT
        )
        surface.blit(title_surf, ((self.screen_w - title_surf.get_width()) // 2, 40))
        surface.blit(sub_surf, ((self.screen_w - sub_surf.get_width()) // 2, 80))

        # Outer pulsing ring
        pulse_r = 30 + int(math.sin(now * 8) * 4)
        pygame.draw.circle(surface, COLOR_ACCENT, (target_x, target_y), pulse_r, width=3)

        # Progress Dwell Arc (0 to 360°)
        if progress > 0.05:
            start_angle = -math.pi / 2
            end_angle = start_angle + (2 * math.pi * progress)
            arc_rect = pygame.Rect(target_x - 35, target_y - 35, 70, 70)
            pygame.draw.arc(surface, COLOR_DWELL_RING, arc_rect, start_angle, end_angle, width=5)

        # Center glowing core dot
        pygame.draw.circle(surface, (255, 255, 255), (target_x, target_y), 8)

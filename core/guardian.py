"""
GazeBoard V2 — Guardian Caregiver Emergency Alert Engine
Listens for Double-Blink events or manual triggers to sound an emergency alarm chime
and present a high-contrast caregiver alert banner.
"""

import math
import time
from typing import Optional

import numpy as np
import pygame


class GuardianEngine:
    """Manages emergency caregiver alarms and alerts."""

    def __init__(self) -> None:
        self.alert_active: bool = False
        self.alert_start_time: float = 0.0
        self.alert_message: str = "EMERGENCY ALARM — CAREGIVER NEEDED!"

        # Create synthesized alarm audio sound via Pygame Mixer
        pygame.mixer.init()
        self._sound: Optional[pygame.mixer.Sound] = self._generate_alarm_sound()

    def _generate_alarm_sound(self) -> Optional[pygame.mixer.Sound]:
        """Generate a synthesized high-contrast 880Hz alert chime."""
        try:
            sample_rate = 44100
            duration = 0.5  # seconds
            n_samples = int(sample_rate * duration)
            buf = np.zeros((n_samples, 2), dtype=np.int16)

            # Two-tone chime (880Hz and 1760Hz)
            for i in range(n_samples):
                t = float(i) / sample_rate
                val = int(16000 * (math.sin(2 * math.pi * 880 * t) + 0.5 * math.sin(2 * math.pi * 1760 * t)))
                buf[i][0] = val
                buf[i][1] = val

            sound = pygame.sndarray.make_sound(buf)
            return sound
        except Exception as e:
            print(f"[Guardian] Audio synthesis fallback: {e}")
            return None

    def trigger_alert(self, reason: str = "DOUBLE-BLINK EMERGENCY") -> None:
        """Trigger emergency alert state and play audio alarm."""
        self.alert_active = True
        self.alert_start_time = time.time()
        self.alert_message = f"🚨 {reason} — CAREGIVER NEEDED!"
        print(f"[Guardian] EMERGENCY ALERT TRIGGERED: {reason}")

        if self._sound:
            try:
                self._sound.play(loops=2)
            except Exception as e:
                print(f"[Guardian] Sound play error: {e}")

    def dismiss(self) -> None:
        """Dismiss active emergency alert."""
        self.alert_active = False

    def draw_alert_banner(self, surface: pygame.Surface, screen_w: int, screen_h: int) -> None:
        """Render high-contrast pulsing caregiver alert banner across the screen."""
        if not self.alert_active:
            return

        now = time.time()

        # Auto-dismiss after 6 seconds
        if now - self.alert_start_time > 6.0:
            self.alert_active = False
            return

        # Pulsing red/yellow banner
        pulse = math.sin(now * 12)
        banner_color = (220, 38, 38) if pulse > 0 else (234, 179, 8)

        rect = pygame.Rect(0, 0, screen_w, 80)
        pygame.draw.rect(surface, banner_color, rect)

        font = pygame.font.SysFont("segoeui", 28, bold=True)
        txt = font.render(self.alert_message, True, (255, 255, 255))
        surface.blit(txt, ((screen_w - txt.get_width()) // 2, 22))

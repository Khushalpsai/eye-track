"""
GazeBoard V2 — Full Standard Keyboard UI Component
Renders a full standard keyboard layout including Numbers (1-0), Symbols (!@#$),
Caps Lock, Enter, Backspace, Spacebar, OS Type toggle, and Caregiver Alarm.
"""

import math
from typing import Dict, List, Tuple

import pygame

from config import (
    COLOR_ACTION_BG,
    COLOR_BG,
    COLOR_DWELL_RING,
    COLOR_KEY_BG,
    COLOR_KEY_BORDER,
    COLOR_KEY_HOVER,
    COLOR_PANEL_BG,
    COLOR_TEXT,
    COLOR_TEXT_SECONDARY,
)


class KeySpec:
    """Specification for a single key element in the layout."""

    def __init__(
        self,
        key_id: str,
        label: str,
        rel_x: float,
        rel_y: float,
        rel_w: float,
        rel_h: float,
        is_action: bool = False,
    ) -> None:
        self.key_id = key_id
        self.label = label
        self.rel_x = rel_x
        self.rel_y = rel_y
        self.rel_w = rel_w
        self.rel_h = rel_h
        self.is_action = is_action


class KeyboardUI:
    """Full standard keyboard interface for eye tracking."""

    def __init__(self, screen_w: int, screen_h: int) -> None:
        self.screen_w = screen_w
        self.screen_h = screen_h

        pygame.font.init()
        self._init_fonts()

        self.text_content: str = ""

        # Keyboard Toggles & Modes
        self.caps_lock_enabled: bool = False
        self.num_symbols_mode: bool = False
        self.os_type_enabled: bool = True
        self.mouse_mode_enabled: bool = False

        # Key definitions and bounding rect cache
        self._key_specs: List[KeySpec] = self._build_layout_specs()
        self._key_rects: Dict[str, pygame.Rect] = {}
        self._recalculate_rects()

    def _init_fonts(self) -> None:
        """Scale font sizes dynamically based on screen height."""
        font_size_key = max(14, int(self.screen_h * 0.034))
        font_size_text = max(18, int(self.screen_h * 0.042))
        font_size_small = max(11, int(self.screen_h * 0.020))

        try:
            self.font_key = pygame.font.SysFont("segoeui", font_size_key, bold=True)
            self.font_text = pygame.font.SysFont("segoeui", font_size_text, bold=True)
            self.font_small = pygame.font.SysFont("segoeui", font_size_small, bold=True)
        except Exception:
            self.font_key = pygame.font.SysFont("sans-serif", font_size_key, bold=True)
            self.font_text = pygame.font.SysFont("sans-serif", font_size_text, bold=True)
            self.font_small = pygame.font.SysFont("sans-serif", font_size_small, bold=True)

    def resize(self, new_w: int, new_h: int) -> None:
        """Dynamically rescale the keyboard layout on window resize."""
        self.screen_w = new_w
        self.screen_h = new_h
        self._init_fonts()
        self._recalculate_rects()

    def _build_layout_specs(self) -> List[KeySpec]:
        """Define standard 5-row full keyboard layout specs."""
        specs: List[KeySpec] = []

        # ── 1. Top Bar: Text Panel & Primary Actions ──────────────────
        specs.append(KeySpec("ACT_BACK", "⌫ BACK", 0.50, 0.04, 0.10, 0.11, is_action=True))
        specs.append(KeySpec("ACT_CLEAR", "🗑 CLEAR", 0.61, 0.04, 0.10, 0.11, is_action=True))
        specs.append(KeySpec("ACT_SPEAK", "🔊 SPEAK", 0.72, 0.04, 0.10, 0.11, is_action=True))
        specs.append(KeySpec("ACT_OSTYPE", "🌐 OS TYPE", 0.83, 0.04, 0.11, 0.11, is_action=True))

        # ── 2. Row 1: Numbers & Main Symbols ─────────────────────────
        num_row = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
        num_w = 0.086
        gap = 0.007
        key_h = 0.13
        x_num_start = (1.0 - (len(num_row) * num_w + (len(num_row) - 1) * gap)) / 2

        for i, num in enumerate(num_row):
            specs.append(KeySpec(f"KEY_NUM_{num}", num, x_num_start + i * (num_w + gap), 0.18, num_w, key_h))

        # ── 3. Row 2: QWERTY Row ──────────────────────────────────────
        row_qwerty = ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"]
        for i, char in enumerate(row_qwerty):
            specs.append(KeySpec(f"KEY_{char}", char, x_num_start + i * (num_w + gap), 0.33, num_w, key_h))

        # ── 4. Row 3: CAPS + ASDF Row + ENTER ─────────────────────────
        row_asdf = ["A", "S", "D", "F", "G", "H", "J", "K", "L"]
        specs.append(KeySpec("ACT_CAPS", "🔒 CAPS", 0.03, 0.48, 0.10, key_h, is_action=True))

        asdf_w = 0.078
        x_asdf_start = 0.14
        for i, char in enumerate(row_asdf):
            specs.append(KeySpec(f"KEY_{char}", char, x_asdf_start + i * (asdf_w + gap), 0.48, asdf_w, key_h))

        specs.append(KeySpec("KEY_ENTER", "↵ ENTER", 0.87, 0.48, 0.10, key_h, is_action=True))

        # ── 5. Row 4: Symbols / Shift + ZXCV Row + Punctuation ────────
        row_zxcv = ["Z", "X", "C", "V", "B", "N", "M"]
        specs.append(KeySpec("ACT_SYMSWITCH", "123 #$%", 0.03, 0.63, 0.10, key_h, is_action=True))

        zxcv_w = 0.078
        x_zxcv_start = 0.14
        for i, char in enumerate(row_zxcv):
            specs.append(KeySpec(f"KEY_{char}", char, x_zxcv_start + i * (zxcv_w + gap), 0.63, zxcv_w, key_h))

        # Punctuation keys
        specs.append(KeySpec("KEY_COMMA", ",", 0.71, 0.63, 0.06, key_h))
        specs.append(KeySpec("KEY_DOT", ".", 0.78, 0.63, 0.06, key_h))
        specs.append(KeySpec("KEY_QUESTION", "?", 0.85, 0.63, 0.06, key_h))
        specs.append(KeySpec("KEY_EXCLAMATION", "!", 0.92, 0.63, 0.05, key_h))

        # ── 6. Row 5: Spacebar & Caregiver Alarm ──────────────────────
        specs.append(KeySpec("KEY_SPACE", "────── SPACEBAR ──────", 0.14, 0.78, 0.65, 0.13, is_action=True))
        specs.append(KeySpec("ACT_GUARDIAN", "🚨 ALARM", 0.81, 0.78, 0.16, 0.13, is_action=True))

        return specs

    def _recalculate_rects(self) -> None:
        """Convert relative layout specs to absolute pixel rects."""
        self._key_rects.clear()
        for spec in self._key_specs:
            x = int(spec.rel_x * self.screen_w)
            y = int(spec.rel_y * self.screen_h)
            w = int(spec.rel_w * self.screen_w)
            h = int(spec.rel_h * self.screen_h)
            self._key_rects[spec.key_id] = pygame.Rect(x, y, w, h)

    def get_key_rects(self) -> Dict[str, pygame.Rect]:
        """Get bounding pixel rects for all key elements."""
        return self._key_rects

    def draw(
        self,
        surface: pygame.Surface,
        active_key_id: str = None,
        dwell_progress: float = 0.0,
    ) -> None:
        """Render the complete standard keyboard UI and radial dwell progress."""
        # 1. Background
        surface.fill(COLOR_BG)

        # 2. Centered Text Display Panel (Top Row)
        text_panel_rect = pygame.Rect(
            int(0.03 * self.screen_w),
            int(0.04 * self.screen_h),
            int(0.45 * self.screen_w),
            int(0.11 * self.screen_h),
        )
        pygame.draw.rect(surface, COLOR_PANEL_BG, text_panel_rect, border_radius=10)
        pygame.draw.rect(surface, (99, 102, 241), text_panel_rect, width=2, border_radius=10)

        # Label above text bar
        top_lbl = self.font_small.render("TYPED SENTENCE:", True, COLOR_TEXT_SECONDARY)
        surface.blit(top_lbl, (text_panel_rect.x + 10, text_panel_rect.y + 2))

        # Render Typed Text Content
        display_str = self.text_content if self.text_content else "Look at keys to type..."
        text_color = COLOR_TEXT if self.text_content else COLOR_TEXT_SECONDARY
        txt_surf = self.font_text.render(display_str, True, text_color)
        surface.blit(txt_surf, (text_panel_rect.x + 14, text_panel_rect.y + 18))

        # 3. Draw All Keys & Controls
        for spec in self._key_specs:
            rect = self._key_rects[spec.key_id]
            is_active = spec.key_id == active_key_id

            label_text = spec.label
            bg_color = COLOR_ACTION_BG if spec.is_action else COLOR_KEY_BG

            # Apply Caps Lock transform to letter labels
            if spec.key_id.startswith("KEY_") and len(spec.key_id) == 5:
                char = spec.key_id[4:]
                if char.isalpha():
                    label_text = char.upper() if self.caps_lock_enabled else char.lower()

            # Dynamic labels and colors for toggles
            if spec.key_id == "ACT_OSTYPE":
                label_text = "🌐 OS: ON" if self.os_type_enabled else "🌐 OS: OFF"
                bg_color = (16, 185, 129) if self.os_type_enabled else (225, 29, 72)
            elif spec.key_id == "ACT_CAPS":
                label_text = "🔒 CAPS ON" if self.caps_lock_enabled else "🔒 CAPS OFF"
                bg_color = (67, 56, 202) if self.caps_lock_enabled else COLOR_ACTION_BG
            elif spec.key_id == "ACT_SYMSWITCH":
                bg_color = (67, 56, 202) if self.num_symbols_mode else COLOR_ACTION_BG
            elif spec.key_id == "ACT_GUARDIAN":
                bg_color = (225, 29, 72)

            pygame.draw.rect(surface, bg_color, rect, border_radius=8)

            # Border
            border_color = COLOR_KEY_HOVER if is_active else COLOR_KEY_BORDER
            border_width = 3 if is_active else 1
            pygame.draw.rect(surface, border_color, rect, width=border_width, border_radius=8)

            # Label
            lbl_surf = self.font_key.render(label_text, True, COLOR_TEXT)
            lbl_x = rect.x + (rect.w - lbl_surf.get_width()) // 2
            lbl_y = rect.y + (rect.h - lbl_surf.get_height()) // 2
            surface.blit(lbl_surf, (lbl_x, lbl_y))

            # Radial Dwell Ring
            if is_active and dwell_progress > 0.0:
                self._draw_radial_fill(surface, rect, dwell_progress)

    def _draw_radial_fill(
        self, surface: pygame.Surface, rect: pygame.Rect, progress: float
    ) -> None:
        """Draw an animated circular progress ring around the active key."""
        center_x = rect.x + rect.w // 2
        center_y = rect.y + rect.h // 2
        radius = min(rect.w, rect.h) // 2 - 4

        pygame.draw.circle(surface, (50, 60, 90), (center_x, center_y), radius, width=3)

        if progress > 0.05:
            start_angle = -math.pi / 2
            end_angle = start_angle + (2 * math.pi * progress)
            arc_rect = pygame.Rect(center_x - radius, center_y - radius, radius * 2, radius * 2)
            pygame.draw.arc(surface, COLOR_DWELL_RING, arc_rect, start_angle, end_angle, width=4)

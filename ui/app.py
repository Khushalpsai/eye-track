"""
GazeBoard V2 — Main Application

Ties together camera capture, face-mesh detection, blink classification,
gaze estimation, Kalman smoothing, and the Pygame rendering loop.
"""

import sys

import pygame

import config
from core.camera import Camera
from core.face_mesh import FaceMeshDetector
from core.blink_detector import BlinkDetector, BlinkType
from core.gaze_estimator import GazeEstimator
from core.kalman_filter import KalmanFilter2D
from ui.gaze_cursor import GazeCursor
from ui.debug_overlay import DebugOverlay


class GazeBoardApp:
    """Main Pygame application for GazeBoard V2.

    Initialises every subsystem (camera, face-mesh, blink detection,
    gaze estimation, Kalman filter) and drives the render loop at the
    configured frame rate.

    Keyboard shortcuts:
        Esc — quit
        D   — toggle debug overlay
        R   — reset Kalman filter
    """

    def __init__(self) -> None:
        """Set up Pygame, core modules, and UI components."""
        # ── Pygame init ──────────────────────────────────────
        pygame.init()

        if config.FULLSCREEN:
            self.screen: pygame.Surface = pygame.display.set_mode(
                (0, 0), pygame.FULLSCREEN
            )
        else:
            self.screen = pygame.display.set_mode(
                (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
            )

        pygame.display.set_caption("GazeBoard V2")
        self.clock = pygame.time.Clock()

        # ── Core modules ─────────────────────────────────────
        self.camera = Camera()
        self.face_mesh = FaceMeshDetector()
        self.blink_detector = BlinkDetector()
        self.gaze_estimator = GazeEstimator()
        self.kalman_filter = KalmanFilter2D()

        # ── UI components ────────────────────────────────────
        self.gaze_cursor = GazeCursor()
        self.debug_overlay = DebugOverlay()

        # ── State ────────────────────────────────────────────
        self.running: bool = True
        self.fps: float = 0.0
        self._last_gaze: tuple = (config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2)

    # ══════════════════════════════════════════════════════════
    # Main loop
    # ══════════════════════════════════════════════════════════

    def run(self) -> None:
        """Start the main game loop until the user quits."""
        while self.running:
            self._handle_events()
            self._update()
            self._render()
            self.clock.tick(config.TARGET_FPS)
        self._cleanup()

    # ══════════════════════════════════════════════════════════
    # Event handling
    # ══════════════════════════════════════════════════════════

    def _handle_events(self) -> None:
        """Process Pygame events (quit, keyboard shortcuts)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_d:
                    self.debug_overlay.toggle()
                elif event.key == pygame.K_r:
                    self.kalman_filter.reset()
                    print("[App] Kalman filter reset.")

    # ══════════════════════════════════════════════════════════
    # Per-frame update
    # ══════════════════════════════════════════════════════════

    def _update(self) -> None:
        """Run the full perception → estimation → smoothing pipeline."""
        # 1. Capture frame
        success, frame = self.camera.get_frame()
        if not success:
            self.gaze_cursor.update(self._last_gaze[0], self._last_gaze[1], "no_face")
            return

        # 2. Face-mesh detection
        result = self.face_mesh.process(frame)
        if result is None:
            self.gaze_cursor.update(self._last_gaze[0], self._last_gaze[1], "no_face")
            self.debug_overlay.update({
                "fps": self.fps,
                "ear_avg": 0.0,
                "gaze_raw": (0.0, 0.0),
                "gaze_smooth": (0.0, 0.0),
                "blink_state": "open",
                "face_detected": False,
                "landmarks_px": [],
            })
            return

        # 3. Blink detection
        blink_event = self.blink_detector.update(
            result.left_eye, result.right_eye
        )

        if blink_event is not None:
            if blink_event.blink_type == BlinkType.LONG:
                print(
                    f"[App] Long blink detected — "
                    f"{blink_event.duration_ms:.0f} ms"
                )
            elif blink_event.blink_type == BlinkType.DOUBLE:
                print(
                    f"[App] Double blink detected — "
                    f"{blink_event.duration_ms:.0f} ms"
                )

        # 4. Gaze estimation
        raw_gaze = self.gaze_estimator.estimate(
            result.left_iris_center, result.right_iris_center
        )

        # 5. Kalman smoothing
        smoothed_gaze = self.kalman_filter.update(raw_gaze)
        self._last_gaze = smoothed_gaze

        # 6. Update cursor
        self.gaze_cursor.update(smoothed_gaze[0], smoothed_gaze[1], "tracking")

        # 7. Feed debug overlay
        ear_left = BlinkDetector.calculate_ear(result.left_eye)
        ear_right = BlinkDetector.calculate_ear(result.right_eye)
        self.debug_overlay.update({
            "fps": self.fps,
            "ear_left": ear_left,
            "ear_right": ear_right,
            "ear_avg": self.blink_detector.current_ear,
            "gaze_raw": raw_gaze,
            "gaze_smooth": smoothed_gaze,
            "blink_state": "closed" if self.blink_detector.is_eyes_closed else "open",
            "face_detected": True,
            "landmarks_px": result.all_landmarks_px,
        })

    # ══════════════════════════════════════════════════════════
    # Rendering
    # ══════════════════════════════════════════════════════════

    def _render(self) -> None:
        """Draw background, grid, cursor, and debug overlay."""
        # Background
        self.screen.fill(config.BG_COLOR)

        # Subtle reference grid
        self._draw_grid()

        # Gaze cursor
        self.gaze_cursor.draw(self.screen)

        # Debug overlay (drawn last so it sits on top)
        self.debug_overlay.draw(self.screen)

        pygame.display.flip()

        # Track FPS for next frame's debug data
        self.fps = self.clock.get_fps()

    def _draw_grid(self) -> None:
        """Draw subtle grid lines across the screen for visual reference."""
        w = self.screen.get_width()
        h = self.screen.get_height()
        spacing = 80  # pixels between grid lines

        for x in range(0, w, spacing):
            pygame.draw.line(
                self.screen, config.GRID_COLOR, (x, 0), (x, h)
            )
        for y in range(0, h, spacing):
            pygame.draw.line(
                self.screen, config.GRID_COLOR, (0, y), (w, y)
            )

    # ══════════════════════════════════════════════════════════
    # Cleanup
    # ══════════════════════════════════════════════════════════

    def _cleanup(self) -> None:
        """Release hardware resources and shut down Pygame."""
        self.camera.release()
        self.face_mesh.release()
        pygame.quit()

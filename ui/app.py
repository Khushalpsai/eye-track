"""
GazeBoard V2 — Main Application (Phase 4 Full System Integration)

Ties together camera perception, face-mesh, blink classification, gaze estimation,
Kalman smoothing, self-healing calibration, selection engine, keyboard UI,
non-blocking TTS, Windows OS input controller (pynput), and Guardian emergency alert engine.
"""

import sys
import pygame

import config
from core.blink_detector import BlinkDetector, BlinkType
from core.camera import Camera
from core.face_mesh import FaceMeshDetector
from core.gaze_estimator import GazeEstimator
from core.guardian import GuardianEngine
from core.kalman_filter import KalmanFilter2D
from core.nudge_calibration import NudgeCalibrationEngine
from core.os_controller import OSController
from core.selection_engine import SelectionEngine
from core.tts import TTSEngine, ToneType
from ui.bootstrapper import QuickBootstrapper
from ui.debug_overlay import DebugOverlay
from ui.gaze_cursor import GazeCursor
from ui.keyboard import KeyboardUI


class GazeBoardApp:
    """Main Pygame application for GazeBoard V2."""

    def __init__(self) -> None:
        """Set up Pygame, perception modules, OS controller, Guardian engine, and UI."""
        pygame.init()

        # Auto-detect actual screen resolution for full-width docking
        import ctypes
        desktop_w = ctypes.windll.user32.GetSystemMetrics(0)
        desktop_h = ctypes.windll.user32.GetSystemMetrics(1)

        w = desktop_w if getattr(config, "DOCK_BOTTOM", False) else config.SCREEN_WIDTH
        h = config.SCREEN_HEIGHT

        if config.FULLSCREEN:
            self.screen: pygame.Surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF, vsync=0)
            w, h = self.screen.get_size()
        else:
            self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE | pygame.DOUBLEBUF, vsync=0)

        pygame.display.set_caption("GazeBoard V2")
        self.clock = pygame.time.Clock()

        # Position window: Always-On-Top + Dock to bottom of screen
        if config.ALWAYS_ON_TOP:
            self._set_always_on_top()
        if getattr(config, "DOCK_BOTTOM", False):
            self._dock_to_bottom(w, h, desktop_h)

        # Perception modules
        self.camera = Camera()
        self.face_mesh = FaceMeshDetector()
        self.blink_detector = BlinkDetector()
        self.gaze_estimator = GazeEstimator()
        self.kalman_filter = KalmanFilter2D()

        # Phase 3 Calibration & Phase 4 System Controllers
        self.nudge_engine = NudgeCalibrationEngine(w, h)
        self.selection_engine = SelectionEngine()
        self.tts = TTSEngine()
        self.os_controller = OSController()
        self.guardian = GuardianEngine()

        # UI components
        self.keyboard_ui = KeyboardUI(w, h)
        self.bootstrapper = QuickBootstrapper(w, h)
        self.gaze_cursor = GazeCursor()
        self.debug_overlay = DebugOverlay()

        # State variables
        self.running: bool = True
        self.fps: float = 0.0
        self._last_gaze: tuple = (w / 2, h / 2)
        self._render_gaze: tuple = (w / 2, h / 2)
        self._active_key_id: str = None
        self._dwell_progress: float = 0.0

    def run(self) -> None:
        """Start the main game loop."""
        while self.running:
            self._handle_events()
            self._update()
            self._render()
            self.clock.tick()
        self._cleanup()

    def _handle_events(self) -> None:
        """Process Pygame events (quit, keyboard shortcuts, window resize)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                w, h = event.w, event.h
                self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE | pygame.DOUBLEBUF, vsync=0)
                self.keyboard_ui.resize(w, h)
                self.nudge_engine.screen_w = w
                self.nudge_engine.screen_h = h
                self.bootstrapper.screen_w = w
                self.bootstrapper.screen_h = h
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_d:
                    self.debug_overlay.toggle()
                elif event.key == pygame.K_c:
                    self.bootstrapper.start()
                elif event.key == pygame.K_r:
                    self.kalman_filter.reset()
                    self.nudge_engine.reset()
                    print("[App] Kalman filter and Nudge engine reset.")

    def _update(self) -> None:
        """Run perception → self-healing calibration → OS control → selection → UI update loop."""
        # 1. Capture camera frame
        success, frame = self.camera.get_frame()
        if success:
            self.face_mesh.submit_frame(frame)

        # 2. Retrieve latest AI face mesh result
        result = self.face_mesh.get_latest_result()
        is_long_blink = False

        if result is not None:
            # Blink detection
            blink_event = self.blink_detector.update(result.left_eye, result.right_eye)
            if blink_event:
                if blink_event.blink_type == BlinkType.LONG:
                    is_long_blink = True
                    print(f"[App] Long Blink Triggered ({blink_event.duration_ms:.0f} ms)")
                elif blink_event.blink_type == BlinkType.DOUBLE:
                    print("[Guardian] Double-Blink Emergency Event Detected!")
                    self.guardian.trigger_alert("DOUBLE-BLINK EMERGENCY")

            # Gaze estimation & Kalman smoothing
            raw_gaze = self.gaze_estimator.estimate(result.left_iris_center, result.right_iris_center)
            smoothed_gaze = self.kalman_filter.update(raw_gaze)

            # Apply Implicit Self-Healing Calibration Nudge Offsets if enabled
            if config.ENABLE_NUDGE_CALIBRATION:
                ox, oy = self.nudge_engine.get_offset(smoothed_gaze[0], smoothed_gaze[1])
            else:
                ox, oy = 0.0, 0.0

            calibrated_gaze = (smoothed_gaze[0] + ox, smoothed_gaze[1] + oy)

            self._last_gaze = calibrated_gaze
            cursor_state = "tracking"

            # Telemetry feed
            ear_left = BlinkDetector.calculate_ear(result.left_eye)
            ear_right = BlinkDetector.calculate_ear(result.right_eye)
            self.debug_overlay.update({
                "fps": self.fps,
                "ear_left": ear_left,
                "ear_right": ear_right,
                "ear_avg": self.blink_detector.current_ear,
                "gaze_raw": raw_gaze,
                "gaze_smooth": calibrated_gaze,
                "calib_conf": self.nudge_engine.confidence_score,
                "blink_state": "closed" if self.blink_detector.is_eyes_closed else "open",
                "face_detected": True,
                "landmarks_px": result.all_landmarks_px,
            })
        else:
            # Fallback to mouse position if camera/face not detected (for easy testing)
            mouse_pos = pygame.mouse.get_pos()
            if mouse_pos != (0, 0):
                self._last_gaze = (float(mouse_pos[0]), float(mouse_pos[1]))
            cursor_state = "no_face"

            self.debug_overlay.update({
                "fps": self.fps,
                "ear_avg": 0.0,
                "gaze_raw": (0.0, 0.0),
                "gaze_smooth": (0.0, 0.0),
                "calib_conf": self.nudge_engine.confidence_score,
                "blink_state": "open",
                "face_detected": False,
                "landmarks_px": [],
            })

        # 3. 5-Second Quick Bootstrapper update (if active)
        if self.bootstrapper.active:
            seeded = self.bootstrapper.update(self._last_gaze)
            if seeded:
                self.nudge_engine.seed_offsets(seeded)

        # 4. Sub-Frame Motion Interpolation for 0ms-latency max hardware FPS pointer tracking
        target_x, target_y = self._last_gaze
        curr_x, curr_y = self._render_gaze
        smooth_x = curr_x + (target_x - curr_x) * 0.85
        smooth_y = curr_y + (target_y - curr_y) * 0.85
        self._render_gaze = (smooth_x, smooth_y)

        # Move real Windows OS Mouse Pointer if Mouse Mode is active
        if self.os_controller.mouse_mode_enabled:
            self.os_controller.move_os_mouse(smooth_x, smooth_y)

        # Update Cursor position at max hardware FPS
        self.gaze_cursor.update(smooth_x, smooth_y, cursor_state)

        # 5. Selection Engine processing (Dwell & Long Blink Trigger)
        key_rects = self.keyboard_ui.get_key_rects()
        sel_res = self.selection_engine.update(self._render_gaze, is_long_blink, key_rects)

        self._active_key_id = sel_res.active_key_id
        self._dwell_progress = sel_res.dwell_progress

        # 6. Handle Key Trigger Events
        if sel_res.triggered_key_id:
            self._handle_key_trigger(sel_res.triggered_key_id)

    def _handle_key_trigger(self, key_id: str) -> None:
        """Handle key activation, emit Windows OS keystrokes, and register implicit Nudge success."""
        print(f"[Keyboard] Key Triggered: {key_id}")

        # Register Nudge Success Event (Implicit Calibration Learning)
        if config.ENABLE_NUDGE_CALIBRATION:
            rects = self.keyboard_ui.get_key_rects()
            if key_id in rects:
                target_center = rects[key_id].center
                self.nudge_engine.register_success(self._render_gaze, target_center)

        if key_id.startswith("KEY_"):
            spec = key_id[4:]
            if spec == "SPACE":
                self.keyboard_ui.text_content += " "
                self.os_controller.press_space()
            elif spec == "ENTER":
                self.keyboard_ui.text_content += "\n"
                self.os_controller.press_enter()
            elif spec.startswith("NUM_"):
                digit = spec[4:]
                self.keyboard_ui.text_content += digit
                self.os_controller.type_character(digit)
            elif spec == "COMMA":
                self.keyboard_ui.text_content += ","
                self.os_controller.type_character(",")
            elif spec == "DOT":
                self.keyboard_ui.text_content += "."
                self.os_controller.type_character(".")
            elif spec == "QUESTION":
                self.keyboard_ui.text_content += "?"
                self.os_controller.type_character("?")
            elif spec == "EXCLAMATION":
                self.keyboard_ui.text_content += "!"
                self.os_controller.type_character("!")
            else:
                # Letters (A-Z)
                char = spec.upper() if self.keyboard_ui.caps_lock_enabled else spec.lower()
                self.keyboard_ui.text_content += char
                self.os_controller.type_character(char)

        elif key_id == "ACT_CAPS":
            self.keyboard_ui.caps_lock_enabled = not self.keyboard_ui.caps_lock_enabled
            print(f"[Keyboard] Caps Lock Toggled: {self.keyboard_ui.caps_lock_enabled}")

        elif key_id == "ACT_BACK":
            if self.keyboard_ui.text_content:
                self.keyboard_ui.text_content = self.keyboard_ui.text_content[:-1]
            self.os_controller.press_backspace()

        elif key_id == "ACT_CLEAR":
            self.keyboard_ui.text_content = ""

        elif key_id == "ACT_SPEAK":
            sentence = self.keyboard_ui.text_content
            tone = self.keyboard_ui.current_tone
            print(f"[TTS] Speaking aloud ({tone.value}): '{sentence}'")
            self.tts.speak(sentence, tone)

        elif key_id == "ACT_OSTYPE":
            self.os_controller.system_typing_enabled = not self.os_controller.system_typing_enabled
            self.keyboard_ui.os_type_enabled = self.os_controller.system_typing_enabled
            print(f"[OSController] System Typing Enabled: {self.os_controller.system_typing_enabled}")

        elif key_id == "ACT_GUARDIAN":
            self.guardian.trigger_alert("MANUAL CAREGIVER ALARM")

    def _render(self) -> None:
        """Render keyboard UI, gaze cursor, bootstrapper, guardian alert, and debug panel."""
        # 1. Render Keyboard UI with active key focus and radial dwell ring
        self.keyboard_ui.draw(self.screen, self._active_key_id, self._dwell_progress)

        # 2. Render gaze cursor on top
        self.gaze_cursor.draw(self.screen)

        # 3. Render 5-Second Bootstrapper overlay if active
        if self.bootstrapper.active:
            self.bootstrapper.draw(self.screen)

        # 4. Render Guardian emergency alert banner if active
        if self.guardian.alert_active:
            w, h = self.screen.get_size()
            self.guardian.draw_alert_banner(self.screen, w, h)

        # 5. Render debug telemetry overlay
        self.debug_overlay.draw(self.screen)

        pygame.display.flip()
        self.fps = self.clock.get_fps()

    def _set_always_on_top(self) -> None:
        """Make GazeBoard a non-activating floating overlay (like native Windows On-Screen Keyboard)."""
        try:
            import ctypes
            hwnd = pygame.display.get_wm_info().get("window")
            if hwnd:
                user32 = ctypes.windll.user32

                # Apply WS_EX_NOACTIVATE (0x08000000) and WS_EX_TOPMOST (0x00000008)
                GWL_EXSTYLE = -20
                WS_EX_TOPMOST = 0x00000008
                WS_EX_NOACTIVATE = 0x08000000

                style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                new_style = style | WS_EX_TOPMOST | WS_EX_NOACTIVATE
                user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)

                # SetWindowPos with SWP_FRAMECHANGED to apply style immediately
                HWND_TOPMOST = -1
                SWP_NOMOVE = 0x0002
                SWP_NOSIZE = 0x0001
                SWP_NOACTIVATE = 0x0010
                SWP_SHOWWINDOW = 0x0040
                SWP_FRAMECHANGED = 0x0020

                user32.SetWindowPos(
                    hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW | SWP_FRAMECHANGED
                )
                print("[App] Non-activating floating overlay (WS_EX_NOACTIVATE) ACTIVE for all apps!")
        except Exception as e:
            print(f"[App] Always-On-Top warning: {e}")

    def _dock_to_bottom(self, w: int, h: int, desktop_h: int) -> None:
        """Dock GazeBoard to the bottom of the screen like Windows On-Screen Keyboard."""
        try:
            import ctypes
            hwnd = pygame.display.get_wm_info().get("window")
            if hwnd:
                x = 0
                y = desktop_h - h - 40  # 40px for taskbar
                SWP_NOSIZE = 0x0001
                SWP_NOZORDER = 0x0004
                SWP_SHOWWINDOW = 0x0040
                ctypes.windll.user32.SetWindowPos(
                    hwnd, 0, x, y, 0, 0,
                    SWP_NOSIZE | SWP_NOZORDER | SWP_SHOWWINDOW
                )
                print(f"[App] Docked to BOTTOM of screen at ({x}, {y})")
        except Exception as e:
            print(f"[App] Dock warning: {e}")

    def _cleanup(self) -> None:
        """Release hardware and worker resources."""
        self.camera.release()
        self.face_mesh.release()
        self.tts.stop()
        pygame.quit()

"""
GazeBoard V2 — Configuration Constants
All tunable parameters in one place.
"""

# ──────────────────────────────────────────────
# Camera
# ──────────────────────────────────────────────
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# ──────────────────────────────────────────────
# Display
# ──────────────────────────────────────────────
SCREEN_WIDTH = 1366  # Full screen width (auto-adjusted at runtime)
SCREEN_HEIGHT = 480  # Bottom panel height for 5-row full standard keyboard
TARGET_FPS = 0  # 0 = Uncapped (maximum possible hardware FPS)
FULLSCREEN = False  # Set True for deployment
ALWAYS_ON_TOP = True # Keep GazeBoard floating on top of Notepad/Chrome
DOCK_BOTTOM = True   # Dock keyboard to the bottom of the screen

# ──────────────────────────────────────────────
# Blink Detection (EAR)
# ──────────────────────────────────────────────
EAR_THRESHOLD = 0.21          # Below this = eyes closed
NATURAL_BLINK_MIN_MS = 80     # Minimum duration to count as a blink
NATURAL_BLINK_MAX_MS = 300    # Max duration for a natural blink
LONG_BLINK_MIN_MS = 500       # Minimum duration for intentional long blink
LONG_BLINK_MAX_MS = 2000      # Safety cap — beyond this, user may be resting
DOUBLE_BLINK_WINDOW_MS = 500  # Max gap between two blinks to count as double

# ──────────────────────────────────────────────
# Kalman Filter & Dead-Zone Smoothing
# ──────────────────────────────────────────────
KALMAN_PROCESS_NOISE = 0.005      # Lower = smoother tracking, ignores micro-jitter
KALMAN_MEASUREMENT_NOISE = 1.5    # Higher = heavy noise suppression
JITTER_DEADZONE_PX = 12.0         # Ignore movement smaller than 12px (keeps dot still)

# ──────────────────────────────────────────────
# Gaze Cursor
# ──────────────────────────────────────────────
CURSOR_RADIUS = 20
CURSOR_COLOR_TRACKING = (0, 220, 100)      # Green — active tracking
CURSOR_COLOR_LOW_CONF = (255, 200, 50)     # Yellow — low confidence
CURSOR_COLOR_NO_FACE = (220, 50, 50)       # Red — face not detected
CURSOR_ALPHA = 150                          # Semi-transparency (0-255)
CURSOR_PULSE_SPEED = 0.05                   # Pulse animation speed

# ──────────────────────────────────────────────
# Debug Overlay
# ──────────────────────────────────────────────
DEBUG_PANEL_WIDTH = 320
DEBUG_PANEL_HEIGHT = 280
DEBUG_FONT_SIZE = 16
DEBUG_BG_COLOR = (20, 20, 30, 200)         # Dark semi-transparent
DEBUG_TEXT_COLOR = (200, 220, 255)          # Light blue text
DEBUG_ACCENT_COLOR = (100, 200, 255)       # Accent for values

# ──────────────────────────────────────────────
# Self-Healing Calibration Toggle
# ──────────────────────────────────────────────
ENABLE_NUDGE_CALIBRATION = True  # Set False to disable implicit learning anytime
DWELL_TIME_MS = 800           # Time in ms required to dwell on a key to type it
RE_DWELL_COOLDOWN_MS = 500    # Cooldown after typing before key can be dwell-selected again

# ──────────────────────────────────────────────
# UI Palette & Layout (Dark Slate Theme)
# ──────────────────────────────────────────────
COLOR_BG = (15, 17, 26)                  # #0F111A Dark slate background
COLOR_PANEL_BG = (24, 27, 42)            # #181B2A Top panel background
COLOR_KEY_BG = (30, 34, 53)              # #1E2235 Key card background
COLOR_KEY_BORDER = (45, 51, 80)          # Key subtle border
COLOR_KEY_HOVER = (59, 130, 246)         # #3B82F6 Blue hover border glow
COLOR_DWELL_RING = (16, 185, 129)        # #10B981 Green radial dwell progress fill
COLOR_TEXT = (243, 244, 246)             # #F3F4F6 Primary white text
COLOR_TEXT_SECONDARY = (156, 163, 175)   # #9CA3AF Secondary text
COLOR_ACCENT = (99, 102, 241)            # #6366F1 Accent purple
COLOR_ACTION_BG = (37, 99, 235)          # #2563EB Action button background (Speak/Clear)


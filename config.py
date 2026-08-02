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
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
TARGET_FPS = 30
FULLSCREEN = False  # Set True for deployment

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
# Kalman Filter
# ──────────────────────────────────────────────
KALMAN_PROCESS_NOISE = 0.03       # Higher = more responsive, more jitter
KALMAN_MEASUREMENT_NOISE = 0.1    # Higher = smoother, more lag

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
# Colors (UI Theme — Dark Mode)
# ──────────────────────────────────────────────
BG_COLOR = (15, 15, 25)                    # Near-black background
GRID_COLOR = (30, 30, 50)                  # Subtle grid lines

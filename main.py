"""
GazeBoard V2 — Main Entry Point
================================
Launches the GazeBoard eye-tracking accessibility application.
"""

import sys
import traceback

from ui.app import GazeBoardApp


STARTUP_BANNER = r"""
╔══════════════════════════════════════╗
║       GazeBoard V2 — Phase 1        ║
║       Sensor Core Active            ║
╠══════════════════════════════════════╣
║  Controls:                          ║
║    ESC   — Quit                     ║
║    D     — Toggle Debug Overlay     ║
║    R     — Reset Kalman Filter      ║
╚══════════════════════════════════════╝
"""


if __name__ == "__main__":
    print(STARTUP_BANNER)

    try:
        app = GazeBoardApp()
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down GazeBoard...")
    except Exception as e:
        print(f"\n[FATAL] An unexpected error occurred: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

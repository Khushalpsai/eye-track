"""
GazeBoard V2 — Camera Module (Threaded High-FPS)
Wraps cv2.VideoCapture with a dedicated background thread for non-blocking
frame reading and automatic BGR→RGB conversion.
"""

import threading
import time

import cv2
import numpy as np

from config import CAMERA_HEIGHT, CAMERA_INDEX, CAMERA_WIDTH


class Camera:
    """Manages a single video-capture device with threaded background reading.

    Runs frame acquisition on a background thread to prevent OpenCV I/O
    blocking the main rendering/tracking loop.

    Parameters
    ----------
    camera_index : int, optional
        Device index (default from ``config.CAMERA_INDEX``).
    width : int, optional
        Requested capture width (default from ``config.CAMERA_WIDTH``).
    height : int, optional
        Requested capture height (default from ``config.CAMERA_HEIGHT``).
    """

    def __init__(
        self,
        camera_index: int = CAMERA_INDEX,
        width: int = CAMERA_WIDTH,
        height: int = CAMERA_HEIGHT,
        target_fps: int = 240,
    ) -> None:
        self._camera_index = camera_index
        self._width = width
        self._height = height

        self._cap = cv2.VideoCapture(camera_index)

        if not self._cap.isOpened():
            print(
                f"[Camera] WARNING: Unable to open camera at index "
                f"{camera_index}. Frames will be unavailable."
            )
            self._running = False
            return

        # Request high FPS and resolution from camera hardware driver
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self._cap.set(cv2.CAP_PROP_FPS, target_fps)

        self._ret: bool = False
        self._frame_rgb: np.ndarray = np.empty((0, 0, 3), dtype=np.uint8)
        self._lock = threading.Lock()
        self._running: bool = True

        # Start background thread for continuous non-blocking frame retrieval
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()

    def _update_loop(self) -> None:
        """Background thread loop that constantly reads from the webcam."""
        while self._running and self._cap.isOpened():
            ret, frame = self._cap.read()
            if ret and frame is not None:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                with self._lock:
                    self._ret = True
                    self._frame_rgb = frame_rgb
            else:
                with self._lock:
                    self._ret = False
            time.sleep(0)  # Yield thread with 0 latency

    # ── public API ───────────────────────────────────────────

    def get_frame(self) -> tuple[bool, np.ndarray]:
        """Read the latest frame non-blockingly.

        Returns
        -------
        success : bool
            ``True`` if a frame was successfully captured.
        frame : np.ndarray
            The latest captured frame in **RGB** colour order.
        """
        with self._lock:
            return self._ret, self._frame_rgb

    def release(self) -> None:
        """Release the camera and stop the background thread."""
        self._running = False
        if self._cap is not None and self._cap.isOpened():
            self._cap.release()

    # ── properties ───────────────────────────────────────────

    @property
    def is_opened(self) -> bool:
        """Return ``True`` if the camera device is currently open."""
        return self._cap is not None and self._cap.isOpened()

    # ── dunder helpers ───────────────────────────────────────

    def __del__(self) -> None:
        """Ensure resources are freed when the object is collected."""
        self.release()

    def __repr__(self) -> str:
        status = "open" if self.is_opened else "closed"
        return (
            f"Camera(index={self._camera_index}, "
            f"{self._width}x{self._height}, {status})"
        )

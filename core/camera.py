"""
GazeBoard V2 — Camera Module
Wraps cv2.VideoCapture with automatic BGR→RGB conversion and
resolution configuration from project constants.
"""

import cv2
import numpy as np

from config import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT


class Camera:
    """Manages a single video-capture device.

    Opens the camera at the configured index and resolution on
    construction.  If the device cannot be opened, a warning is
    printed and every subsequent ``get_frame()`` call returns
    ``(False, empty_array)``.

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
            return

        # Request the desired resolution (the driver may choose the
        # closest supported size).
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    # ── public API ───────────────────────────────────────────

    def get_frame(self) -> tuple[bool, np.ndarray]:
        """Read one frame from the camera and return it as RGB.

        Returns
        -------
        success : bool
            ``True`` if a frame was successfully captured.
        frame : np.ndarray
            The captured frame in **RGB** colour order.  On failure
            an empty ``(0, 0, 3)`` array is returned.
        """
        if not self.is_opened:
            return False, np.empty((0, 0, 3), dtype=np.uint8)

        success, frame = self._cap.read()

        if not success or frame is None:
            return False, np.empty((0, 0, 3), dtype=np.uint8)

        frame_rgb: np.ndarray = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return True, frame_rgb

    def release(self) -> None:
        """Release the underlying video-capture device."""
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

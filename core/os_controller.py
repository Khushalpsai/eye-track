"""
GazeBoard V2 — System-Wide OS Input Controller
Uses dual-mode injection (Win32 PostMessage + SendInput) to guarantee keystrokes
type directly into Notepad, Chrome, Word, or any background application even when
GazeBoard is open and in focus.
"""

import ctypes
import ctypes.wintypes as wintypes
from typing import List, Optional

from pynput.mouse import Controller as MouseController, Button


# ── Win32 SendInput & Message Constants ──────────────────────────────
INPUT_KEYBOARD = 1
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_KEYUP = 0x0002

WM_CHAR = 0x0102
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
        ("mi", MOUSEINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", _INPUT_UNION),
    ]


def _get_target_windows() -> List[int]:
    """Find target application window handles (Notepad, Chrome, Active App)."""
    user32 = ctypes.windll.user32
    targets: List[int] = []

    # 1. Look for Notepad main window
    np_hwnd = user32.FindWindowW("Notepad", None)
    if np_hwnd:
        # Find child edit control inside Notepad
        edit_hwnd = user32.FindWindowExW(np_hwnd, None, "Edit", None)
        if not edit_hwnd:
            edit_hwnd = user32.FindWindowExW(np_hwnd, None, "RichEditD2DPT", None)
        targets.append(edit_hwnd if edit_hwnd else np_hwnd)

    # 2. Add current foreground window
    fg_hwnd = user32.GetForegroundWindow()
    if fg_hwnd and fg_hwnd not in targets:
        targets.append(fg_hwnd)

    return targets


def _send_unicode_key(char: str) -> None:
    """Inject unicode character into Notepad and active foreground window."""
    user32 = ctypes.windll.user32

    # A. Send via direct Win32 PostMessage (delivers even if Notepad is out of focus)
    targets = _get_target_windows()
    for c in char:
        code = ord(c)
        for hwnd in targets:
            try:
                user32.PostMessageW(hwnd, WM_CHAR, code, 0)
            except Exception:
                pass

    # B. Send via Win32 SendInput (for Chrome, Word, and general OS compatibility)
    inputs = []
    for c in char:
        key_down = INPUT()
        key_down.type = INPUT_KEYBOARD
        key_down.union.ki.wVk = 0
        key_down.union.ki.wScan = ord(c)
        key_down.union.ki.dwFlags = KEYEVENTF_UNICODE
        key_down.union.ki.time = 0
        key_down.union.ki.dwExtraInfo = None
        inputs.append(key_down)

        key_up = INPUT()
        key_up.type = INPUT_KEYBOARD
        key_up.union.ki.wVk = 0
        key_up.union.ki.wScan = ord(c)
        key_up.union.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
        key_up.union.ki.time = 0
        key_up.union.ki.dwExtraInfo = None
        inputs.append(key_up)

    n = len(inputs)
    arr = (INPUT * n)(*inputs)
    user32.SendInput(n, arr, ctypes.sizeof(INPUT))


def _send_vk_key(vk_code: int) -> None:
    """Inject virtual key (Backspace, Enter, Space) into target windows."""
    user32 = ctypes.windll.user32

    # A. Direct PostMessage
    targets = _get_target_windows()
    for hwnd in targets:
        try:
            user32.PostMessageW(hwnd, WM_KEYDOWN, vk_code, 0)
            user32.PostMessageW(hwnd, WM_KEYUP, vk_code, 0)
        except Exception:
            pass

    # B. SendInput
    inputs = []
    key_down = INPUT()
    key_down.type = INPUT_KEYBOARD
    key_down.union.ki.wVk = vk_code
    key_down.union.ki.wScan = 0
    key_down.union.ki.dwFlags = 0
    key_down.union.ki.time = 0
    key_down.union.ki.dwExtraInfo = None
    inputs.append(key_down)

    key_up = INPUT()
    key_up.type = INPUT_KEYBOARD
    key_up.union.ki.wVk = vk_code
    key_up.union.ki.wScan = 0
    key_up.union.ki.dwFlags = KEYEVENTF_KEYUP
    key_up.union.ki.time = 0
    key_up.union.ki.dwExtraInfo = None
    inputs.append(key_up)

    arr = (INPUT * 2)(*inputs)
    user32.SendInput(2, arr, ctypes.sizeof(INPUT))


class OSController:
    """Controls real Windows OS keyboard and mouse inputs via dual-mode injection."""

    def __init__(self) -> None:
        self.mouse = MouseController()
        self.system_typing_enabled: bool = True
        self.mouse_mode_enabled: bool = False

    def type_character(self, char: str) -> None:
        """Inject a character into Notepad, Chrome, and active background windows."""
        if not self.system_typing_enabled or not char:
            return
        try:
            _send_unicode_key(char)
        except Exception as e:
            print(f"[OSController] Keystroke error: {e}")

    def press_backspace(self) -> None:
        """Inject Backspace into target windows."""
        if not self.system_typing_enabled:
            return
        try:
            _send_vk_key(0x08)  # VK_BACK
        except Exception as e:
            print(f"[OSController] Backspace error: {e}")

    def press_space(self) -> None:
        """Inject Spacebar into target windows."""
        if not self.system_typing_enabled:
            return
        try:
            _send_vk_key(0x20)  # VK_SPACE
        except Exception as e:
            print(f"[OSController] Spacebar error: {e}")

    def press_enter(self) -> None:
        """Inject Enter into target windows."""
        if not self.system_typing_enabled:
            return
        try:
            _send_vk_key(0x0D)  # VK_RETURN
        except Exception as e:
            print(f"[OSController] Enter error: {e}")

    def move_os_mouse(self, x: float, y: float) -> None:
        """Move the actual Windows OS mouse pointer."""
        if not self.mouse_mode_enabled:
            return
        try:
            self.mouse.position = (int(x), int(y))
        except Exception as e:
            print(f"[OSController] Mouse move error: {e}")

    def click_os_mouse(self, button: str = "left") -> None:
        """Trigger a real Windows OS click."""
        if not self.mouse_mode_enabled:
            return
        try:
            btn = Button.right if button == "right" else Button.left
            self.mouse.click(btn, 1)
        except Exception as e:
            print(f"[OSController] Mouse click error: {e}")

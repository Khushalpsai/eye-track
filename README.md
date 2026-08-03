# 👁️ GazeBoard V2 — Accessible Eye-Tracking AAC Keyboard & OS Controller

> **GazeBoard V2** is a next-generation, hands-free eye-tracking communication system and Windows OS controller designed for individuals with severe motor impairments or ALS. Built with OpenCV, MediaPipe 1.0, Pygame-CE, and native Win32 APIs, it allows users to type into any application (Google Chrome, WhatsApp Web, Microsoft Word, Notepad) entirely with their eyes.

---

## 🌟 Key Features

- **🎯 Asynchronous Sensor Core**: Uses MediaPipe 1.0 `FaceLandmarker` with 478 face landmarks and dedicated multi-threaded AI worker pipelines running with 0ms camera latency.
- **⚡ Uncapped 500+ FPS Pointer**: Sub-frame motion interpolation ensures the green gaze cursor tracks your eyes with **instant zero-lag response**.
- **⌨️ Full Standard Keyboard**: 5-row standard QWERTY layout featuring:
  - Full Number Row (`1` to `0`)
  - **`🔒 CAPS LOCK`** toggle (dynamically transforms key labels between uppercase and lowercase)
  - **`↵ ENTER`** key & Punctuation (`.`, `,`, `?`, `!`)
  - `123 #$%` Symbols toggle & Spacebar
- **👑 Implicit Self-Healing Calibration**: Eliminates traditional manual calibration walls. A 4-quadrant background learning engine automatically nudges spatial offset grids as posture shifts over time.
- **⏱️ 5-Second Quick Bootstrapper**: Press **`C`** anytime to launch a 4-corner calibration sequence (1 sec per corner) to seed the initial map.
- **🌐 System-Wide Windows OS Control**: Operates as a native Windows Accessibility floating overlay (`WS_EX_NOACTIVATE` + `WS_EX_TOPMOST`). Docks at the bottom of the screen and types live into **Notepad, Chrome, WhatsApp, or Word** without stealing window focus!
- **🚨 Guardian Caregiver Alarm**: Detects rapid **Double-Blinks** to trigger a synthesized 880Hz two-tone emergency chime and visual alert banner.
- **🔊 Non-Blocking Text-to-Speech**: Integrated `pyttsx3` speech synthesis running on a queue-backed background thread.

---

## 🛠️ Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                        GAZEBOARD V2 PIPELINE                           │
└────────────────────────────────────────────────────────────────────────┘
                                   │
┌────────────────────────┐  ┌──────▼─────────────────┐  ┌─────────────────┐
│ Thread 1: Camera       ├──► Thread 2: MediaPipe AI ├──► Thread 3: Pygame │
│ (OpenCV Capture 0ms)   │  │ (FaceLandmarker 478)    │  │ (Render 500 FPS)│
└────────────────────────┘  └─────────────────────────┘  └────────┬────────┘
                                                                  │
      ┌───────────────────────────────────────────────────────────┴───┐
      │                                                               │
┌─────▼────────────────────────┐                             ┌────────▼────────┐
│ Implicit Nudge Calibration   │                             │ Selection Engine│
│ (4-Quadrant Spatial Learning)│                             │ (800ms Dwell)   │
└─────────────┬────────────────┘                             └────────┬────────┘
              │                                                       │
              └───────────────────────────┬───────────────────────────┘
                                          │
                            ┌─────────────▼─────────────┐
                            │ Dual-Mode Win32 Injection │
                            │ (PostMessage + SendInput) │
                            └─────────────┬─────────────┘
                                          │
                ┌─────────────────────────┴─────────────────────────┐
                │                                                   │
     ┌──────────▼───────────┐                            ┌──────────▼───────────┐
     │ Target Laptop App    │                            │ Thread 4: TTS Worker │
     │ (Chrome, Word, etc)  │                            │ (Speech Synthesis)   │
     └──────────────────────┘                            └──────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+** (Tested on Python 3.14.3 on Windows)
- Webcam (built-in or USB)

### Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Khushalpsai/eye-track.git
   cd eye-track
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run GazeBoard V2**:
   ```bash
   python main.py
   ```

---

## ⌨️ How to Use

1. **System-Wide Laptop Typing**:
   - Open **Notepad**, **Google Chrome**, or **WhatsApp Web** in the background.
   - Run `python main.py`. GazeBoard docks at the bottom of your screen as a floating overlay.
   - Click inside Notepad or Chrome once to place your cursor.
   - Look at keys on GazeBoard — characters will type **directly into Notepad or Chrome in real time**!

2. **Keyboard Shortcuts**:
   - **`C`**: Launch the **5-Second Quick Bootstrapper** (stare at the 4 glowing corner dots).
   - **`D`**: Toggle the **Telemetry Debug Overlay** (FPS counter, EAR bar graph, Calibration Confidence rating).
   - **`R`**: Reset Kalman filter and Nudge calibration engine.
   - **`ESC`**: Quit GazeBoard.

---

## 📁 Repository Structure

```
eye-track/
├── config.py                 # Central configuration parameters
├── main.py                   # Launcher entry point
├── requirements.txt          # Dependencies (pygame-ce, mediapipe, opencv-python, pynput, pyttsx3)
├── README.md                 # Project documentation
├── core/
│   ├── camera.py             # Threaded OpenCV video capture
│   ├── face_mesh.py          # Asynchronous MediaPipe 1.0 FaceLandmarker worker
│   ├── blink_detector.py     # EAR blink classifier (Natural, Long, Double)
│   ├── gaze_estimator.py     # Gaze coordinate estimator
│   ├── kalman_filter.py      # Constant-velocity 2D Kalman smoothing
│   ├── nudge_calibration.py  # Self-healing 4-quadrant background learning engine
│   ├── os_controller.py      # Dual-mode Win32 SendInput & PostMessage controller
│   ├── guardian.py           # Caregiver emergency audio alarm engine
│   ├── selection_engine.py   # Dwell time selection & long-blink trigger engine
│   └── tts.py                # Queue-backed text-to-speech engine
├── ui/
│   ├── app.py                # Main Pygame application engine & WS_EX_NOACTIVATE overlay
│   ├── keyboard.py           # Full standard 5-row keyboard UI renderer
│   ├── bootstrapper.py       # 5-second 4-corner quick calibration UI
│   ├── gaze_cursor.py        # High-FPS animated gaze cursor
│   └── debug_overlay.py      # Real-time telemetry dashboard
└── utils/
    └── landmarks.py          # MediaPipe 478 landmark index reference arrays
```

---

## 🛡️ License

Distributed under the MIT License. See `LICENSE` for more information.

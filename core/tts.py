"""
GazeBoard V2 — Text-to-Speech Engine
Runs pyttsx3 in a background thread to prevent audio speech calls from
blocking the Pygame UI render loop. Supports 4 emotional prosody tones.
"""

import queue
import threading
from enum import Enum

import pyttsx3


class ToneType(Enum):
    """Vocal emotional prosody profiles."""

    NEUTRAL = "Neutral 💬"
    URGENT = "Urgent 🚨"
    WARM = "Warm 😊"
    JOKING = "Joking 😜"


class TTSEngine:
    """Non-blocking Text-to-Speech engine supporting emotional tone profiles."""

    def __init__(self) -> None:
        self._speech_queue: queue.Queue = queue.Queue()
        self._running: bool = True

        # Start background worker thread for TTS calls
        self._worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self._worker_thread.start()

    def speak(self, text: str, tone: ToneType = ToneType.NEUTRAL) -> None:
        """Queue text to be spoken aloud in the specified tone."""
        if not text or not text.strip():
            return
        self._speech_queue.put((text.strip(), tone))

    def _speech_worker(self) -> None:
        """Background thread loop that initializes pyttsx3 and consumes speech requests."""
        try:
            engine = pyttsx3.init()
        except Exception as e:
            print(f"[TTS] WARNING: Could not initialize pyttsx3 engine: {e}")
            return

        while self._running:
            try:
                text, tone = self._speech_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            try:
                # Configure voice prosody based on selected tone
                if tone == ToneType.URGENT:
                    engine.setProperty("rate", 220)
                    engine.setProperty("volume", 1.0)
                elif tone == ToneType.WARM:
                    engine.setProperty("rate", 135)
                    engine.setProperty("volume", 0.9)
                elif tone == ToneType.JOKING:
                    engine.setProperty("rate", 185)
                    engine.setProperty("volume", 1.0)
                else:  # NEUTRAL
                    engine.setProperty("rate", 160)
                    engine.setProperty("volume", 1.0)

                engine.say(text)
                engine.runAndWait()
            except Exception as err:
                print(f"[TTS] Error during speech synthesis: {err}")
            finally:
                self._speech_queue.task_done()

    def stop(self) -> None:
        """Stop the speech worker thread."""
        self._running = False

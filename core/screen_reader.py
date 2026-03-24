"""
Screenshot + OCR reader for PoELens.

User-initiated only (hotkey or button click). Never runs autonomously.
Captures the screen, feeds it to Windows OCR (winrt), and returns raw text.

TOS note: user-triggered screen capture is the same tier as Lailloken UI
(Tier 2 / passive reading) and is permitted under GGG policy.

Windows OCR (winrt) is built into Windows 10+ — no extra install beyond
the 'winrt' Python package (pip install winrt).
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import threading
from typing import Callable, Optional

try:
    import mss
    _MSS_AVAILABLE = True
except ImportError:
    _MSS_AVAILABLE = False

try:
    from PIL import Image
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

_WINRT_AVAILABLE = False
try:
    import winrt.windows.media.ocr as _winrt_ocr
    import winrt.windows.graphics.imaging as _winrt_imaging
    import winrt.windows.storage as _winrt_storage
    import winrt.windows.storage.streams as _winrt_streams
    _WINRT_AVAILABLE = True
except ImportError:
    pass


def is_available() -> bool:
    """True if screenshot + OCR is runnable on this system."""
    return _MSS_AVAILABLE and _PIL_AVAILABLE and _WINRT_AVAILABLE


def capture_screen(monitor: int = 1) -> Optional["Image.Image"]:
    """
    Capture the specified monitor (1-indexed) and return a PIL Image.
    Returns None if mss or Pillow is unavailable.
    """
    if not _MSS_AVAILABLE or not _PIL_AVAILABLE:
        return None
    try:
        with mss.mss() as sct:
            monitors = sct.monitors  # index 0 = all combined, 1+ = individual
            idx = min(monitor, max(1, len(monitors) - 1))
            raw = sct.grab(monitors[idx])
            return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
    except Exception as e:
        print(f"[ScreenReader] Capture failed: {e}")
        return None


def ocr_image_file(png_path: str) -> Optional[str]:
    """
    Run Windows OCR on a PNG file (synchronous, runs async loop in a thread).
    Returns extracted text or None on failure.
    """
    if not _WINRT_AVAILABLE:
        return None

    result: list[str] = []
    error: list[Exception] = []

    def _run():
        try:
            loop = asyncio.new_event_loop()
            text = loop.run_until_complete(_ocr_file_async(png_path))
            loop.close()
            result.append(text)
        except Exception as e:
            error.append(e)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=15)

    if error:
        print(f"[ScreenReader] OCR failed: {error[0]}")
        return None
    return result[0] if result else None


async def _ocr_file_async(png_path: str) -> str:
    """Async implementation: load PNG via WinRT StorageFile → OCR."""
    file = await _winrt_storage.StorageFile.get_file_from_path_async(png_path)
    stream = await file.open_async(_winrt_storage.FileAccessMode.READ)
    decoder = await _winrt_imaging.BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()

    # WinRT OCR requires Bgra8 or Gray8 pixel format
    if bitmap.bitmap_pixel_format != _winrt_imaging.BitmapPixelFormat.BGRA8:
        bitmap = _winrt_imaging.SoftwareBitmap.convert(
            bitmap, _winrt_imaging.BitmapPixelFormat.BGRA8
        )

    engine = _winrt_ocr.OcrEngine.try_create_from_user_profile_languages()
    if engine is None:
        return ""
    ocr_result = await engine.recognize_async(bitmap)
    return ocr_result.text


class ScreenReader:
    """
    High-level screen reader. Call scan() to capture + OCR in a background
    thread. Results are delivered via on_result callbacks.
    """

    def __init__(self):
        self._on_result: list[Callable] = []

    def on_result(self, callback: Callable):
        """Register callback({"text": str | None, "error": str | None})."""
        self._on_result.append(callback)

    def scan(self, monitor: int = 1):
        """
        Capture and OCR the screen in a background thread.
        Results are delivered via on_result callbacks.
        Does nothing if the required packages are not installed.
        """
        if not is_available():
            self._emit(None, "Screen OCR not available — install mss and winrt packages.")
            return
        threading.Thread(target=self._do_scan, args=(monitor,), daemon=True).start()

    def _do_scan(self, monitor: int):
        image = capture_screen(monitor)
        if image is None:
            self._emit(None, "Screen capture failed.")
            return

        # Save to a temp file so WinRT StorageFile can load it (requires absolute path)
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp_path = tmp.name
        tmp.close()
        try:
            image.save(tmp_path, format="PNG")
            # WinRT needs backslashes and absolute path
            abs_path = os.path.abspath(tmp_path).replace("/", "\\")
            text = ocr_image_file(abs_path)
            if text is None:
                self._emit(None, "OCR failed — Windows OCR may not be available.")
            else:
                self._emit(text, None)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def _emit(self, text: Optional[str], error: Optional[str]):
        result = {"text": text, "error": error}
        for cb in self._on_result:
            try:
                cb(result)
            except Exception as e:
                print(f"[ScreenReader] callback error: {e}")

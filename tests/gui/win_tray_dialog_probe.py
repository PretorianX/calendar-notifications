"""Windows probe: open Settings from the real tray icon and check it responds.

Run as a script: ``python tests/gui/win_tray_dialog_probe.py <mode>``.

Modes:
- ``menu``: right-click the tray icon, pick "Settings" with the keyboard.
- ``direct``: call the Settings handler from the tray icon's message handler.

The probe starts the real ``TrayApp``. A watcher thread plays the user: it opens
the dialog, clicks "Cancel" with real mouse input and waits for the dialog to
close. Exit code 0 means the dialog responded. Any other code means it did not.
"""

import ctypes
import faulthandler
import os
import sys
import threading
import time
from ctypes import wintypes

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from PyQt6 import QtCore  # noqa: E402

from src.gui import tray_app  # noqa: E402

TITLE = "Calendar Notifications Settings"
WM_NULL = 0x0000
WM_CLOSE = 0x0010
WM_KEYDOWN = 0x0100
WM_RBUTTONUP = 0x0205
WM_PYSTRAY_NOTIFY = 0x0400 + 11
WM_PROBE_SETTINGS = 0x0400 + 50
VK_RETURN = 0x0D
VK_DOWN = 0x28
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
KEYEVENTF_KEYUP = 0x0002
SMTO_ABORTIFHUNG = 0x0002
# "Settings" is the third item of the tray menu.
SETTINGS_MENU_INDEX = 3

user32 = ctypes.windll.user32  # type: ignore[attr-defined]
user32.FindWindowW.restype = wintypes.HWND
user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.PostMessageW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsHungAppWindow.argtypes = [wintypes.HWND]
user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
user32.SendMessageTimeoutW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
    wintypes.UINT,
    wintypes.UINT,
    ctypes.POINTER(ctypes.c_size_t),
]

# Centre of the Cancel button in physical client pixels, set when the dialog shows.
cancel_point: list[int] = []


def log(message: str) -> None:
    print(f"PROBE {message}", flush=True)


def _record_cancel_point(dialog, event) -> None:
    centre = dialog.cancel_button.mapTo(dialog, dialog.cancel_button.rect().center())
    ratio = dialog.devicePixelRatioF()
    cancel_point[:] = [int(centre.x() * ratio), int(centre.y() * ratio)]
    log(f"dialog showEvent on thread {threading.current_thread().name}")


def _wait(condition, timeout: float):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = condition()
        if value:
            return value
        time.sleep(0.1)
    return None


def _dialog_hwnd():
    hwnd = user32.FindWindowW(None, TITLE)
    return hwnd if hwnd and user32.IsWindowVisible(hwnd) else None


def _open_from_menu(icon) -> None:
    user32.PostMessageW(icon._hwnd, WM_PYSTRAY_NOTIFY, 0, WM_RBUTTONUP)
    menu = _wait(lambda: user32.FindWindowW("#32768", None), 10)
    log(f"popup menu window: {menu}")
    if not menu:
        return
    time.sleep(0.5)
    for key in [VK_DOWN] * SETTINGS_MENU_INDEX + [VK_RETURN]:
        user32.PostMessageW(menu, WM_KEYDOWN, key, 0)
        time.sleep(0.2)
    if _wait(_dialog_hwnd, 5):
        return
    log("posted keys did not open the dialog, sending real key input")
    for key in [VK_DOWN] * SETTINGS_MENU_INDEX + [VK_RETURN]:
        user32.keybd_event(key, 0, 0, 0)
        user32.keybd_event(key, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.2)


def _open_direct(app, icon) -> None:
    icon._message_handlers[WM_PROBE_SETTINGS] = lambda _w, _l: app._show_settings()
    user32.PostMessageW(icon._hwnd, WM_PROBE_SETTINGS, 0, 0)


def _watch(app, mode: str) -> None:
    code = 1
    try:
        icon = _wait(
            lambda: (
                app.tray_icon
                if getattr(app.tray_icon, "_hwnd", None) and app.tray_icon.visible
                else None
            ),
            20,
        )
        if icon is None:
            log("RESULT tray icon not ready")
            return
        time.sleep(1)

        if mode == "menu":
            _open_from_menu(icon)
        else:
            _open_direct(app, icon)

        hwnd = _wait(_dialog_hwnd, 15)
        if not hwnd:
            log("RESULT dialog not shown")
            code = 2
            return
        time.sleep(1.5)
        log(f"dialog hwnd {hwnd}, IsHungAppWindow={user32.IsHungAppWindow(hwnd)}")

        point = wintypes.POINT(*cancel_point) if cancel_point else None
        if point is not None:
            user32.ClientToScreen(hwnd, ctypes.byref(point))
            user32.SetCursorPos(point.x, point.y)
            time.sleep(0.3)
            user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            log(f"clicked Cancel at {point.x},{point.y}")
        if _wait(lambda: not _dialog_hwnd(), 5):
            log("RESULT responsive: Cancel click closed the dialog")
            code = 0
            return

        reply = ctypes.c_size_t()
        answered = user32.SendMessageTimeoutW(
            hwnd, WM_NULL, 0, 0, SMTO_ABORTIFHUNG, 3000, ctypes.byref(reply)
        )
        log(f"Cancel click ignored. WM_NULL answered={bool(answered)}")
        user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        closed = bool(_wait(lambda: not _dialog_hwnd(), 5))
        log(f"WM_CLOSE closed the dialog={closed}")
        log(f"IsHungAppWindow={user32.IsHungAppWindow(hwnd)}")
        log("RESULT unresponsive")
        code = 3
    finally:
        if code != 0:
            faulthandler.dump_traceback(file=sys.stdout, all_threads=True)
        sys.stdout.flush()
        os._exit(code)


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "menu"
    tray_app.SettingsDialog.showEvent = _record_cancel_point  # type: ignore[method-assign]
    tray_app.setup_logging()
    app = tray_app.TrayApp()
    log(f"Qt {QtCore.QT_VERSION_STR}, platform {app.qt_app.platformName()}")
    threading.Thread(target=_watch, args=(app, mode), daemon=True).start()
    app.run()


if __name__ == "__main__":
    main()

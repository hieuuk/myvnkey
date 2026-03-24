"""Monitor the foreground application and auto-switch Vietnamese mode."""

import ctypes
import ctypes.wintypes as wintypes
import os
import re
import threading
import time

import config

# ── Win32 API ────────────────────────────────────────────────────────────────

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def get_foreground_process_name():
    """Return the executable name (e.g. 'Discord.exe') of the foreground window.
    Returns None if detection fails.
    """
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None

    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value == 0:
        return None

    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not handle:
        return None

    try:
        buf = ctypes.create_unicode_buffer(512)
        size = wintypes.DWORD(512)
        ok = kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size))
        if ok and size.value > 0:
            return os.path.basename(buf.value)
    finally:
        kernel32.CloseHandle(handle)

    return None


def get_foreground_window_title():
    """Return the window title of the foreground window.
    Returns None if detection fails.
    """
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return None
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value or None


def get_foreground_info():
    """Return (process_name, window_title) for the foreground window."""
    return get_foreground_process_name(), get_foreground_window_title()


# ── Rule matching ────────────────────────────────────────────────────────────

def _match_rule(rule, process_name, window_title):
    """Check if a single rule matches. Returns True/False."""
    match_type = rule.get('match', 'process')
    pattern = rule.get('pattern', '')
    if not pattern:
        return False

    if match_type == 'process':
        return pattern.lower() == (process_name or '').lower()
    elif match_type == 'title':
        return pattern.lower() in (window_title or '').lower()
    elif match_type == 'regex':
        try:
            return bool(re.search(pattern, window_title or '', re.IGNORECASE))
        except re.error:
            return False
    return False


def find_matching_rule(process_name, window_title):
    """Find the first matching rule. Order: regex, title, process.
    Returns the rule dict or None.
    """
    # More specific rules first: regex > title contains > process name
    for match_type in ('regex', 'title', 'process'):
        for rule in config.app_rules:
            if rule.get('match', 'process') == match_type:
                if _match_rule(rule, process_name, window_title):
                    return rule

    return None


# ── App monitor thread ───────────────────────────────────────────────────────

class AppMonitor:
    def __init__(self, on_mode_change=None, poll_interval=0.2):
        self._on_mode_change = on_mode_change
        self._poll_interval = poll_interval
        self._last_hwnd = None
        self._running = False
        self._thread = None

    def start(self):
        """Start the monitor in a daemon thread."""
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _poll_loop(self):
        while self._running:
            try:
                self._check_foreground()
            except Exception:
                pass
            time.sleep(self._poll_interval)

    def _check_foreground(self):
        hwnd = user32.GetForegroundWindow()
        if not hwnd or hwnd == self._last_hwnd:
            return
        self._last_hwnd = hwnd

        proc, title = get_foreground_info()
        rule = find_matching_rule(proc, title)

        if rule is not None:
            vn_enabled = rule['vietnamese']
            if config.vietnamese_mode != vn_enabled:
                config.vietnamese_mode = vn_enabled
                self._notify()
        else:
            # Not in rules: use default_mode (last Alt+Z state)
            if config.vietnamese_mode != config.default_mode:
                config.vietnamese_mode = config.default_mode
                self._notify()

    def _notify(self):
        if self._on_mode_change:
            self._on_mode_change()

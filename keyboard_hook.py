"""Global keyboard hook for Vietnamese Telex input using pynput.

Uses a non-suppressed listener. Simulated events are tracked via a skip
counter so the hook ignores its own injected keystrokes.
"""

import threading
from pynput import keyboard
from pynput.keyboard import Key, KeyCode, Controller

import config
import telex_engine


class KeyboardHandler:
    def __init__(self, on_mode_change=None):
        self.controller = Controller()
        self.buffer = []
        self._skip_events = 0
        self._pressed_keys = set()
        self._on_mode_change = on_mode_change
        self._listener = None
        self._lock = threading.Lock()

    def start(self):
        """Start the keyboard listener (blocking)."""
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.start()
        self._listener.join()

    def stop(self):
        """Stop the keyboard listener."""
        if self._listener:
            self._listener.stop()

    def _on_press(self, key):
        with self._lock:
            # Skip events that we injected ourselves
            if self._skip_events > 0:
                self._skip_events -= 1
                return

            # Track pressed keys for hotkey detection
            self._pressed_keys.add(key)

            # Alt+Z toggle
            if self._check_toggle():
                return

            # Get the character if it's a printable key
            char = self._get_char(key)

            if char is None:
                # Special key (Enter, Backspace, arrows, etc.)
                if key == Key.backspace and self.buffer:
                    self.buffer.pop()
                elif key in (Key.enter, Key.tab, Key.space):
                    self.buffer.clear()
                else:
                    if key not in (Key.shift, Key.shift_r, Key.ctrl_l, Key.ctrl_r,
                                   Key.alt_l, Key.alt_r, Key.alt_gr, Key.caps_lock,
                                   Key.cmd, Key.cmd_r):
                        self.buffer.clear()
                return

            # Word-break character
            if char in config.WORD_BREAK_CHARS:
                self.buffer.clear()
                return

            # Not in Vietnamese mode: just track the buffer
            if not config.vietnamese_mode:
                self.buffer.append(char)
                return

            # Process through Telex engine
            old_buffer = self.buffer[:]
            new_buffer, backspace_count = telex_engine.process_key(self.buffer, char)

            if backspace_count == 0:
                self.buffer = new_buffer
                return

            # Transformation needed.
            self.buffer = new_buffer
            total_bs = backspace_count + 1

            diff_start = len(old_buffer) - backspace_count
            if diff_start < 0:
                diff_start = 0
            new_text = ''.join(new_buffer[diff_start:])

            # Skip counter for our injected events
            self._skip_events = total_bs + len(new_text)

        # Release lock before sending keys
        self._replace_keystroke(total_bs, new_text)

    def _on_release(self, key):
        self._pressed_keys.discard(key)

    def _check_toggle(self):
        """Check if Alt+Z is pressed to toggle Vietnamese mode."""
        alt_pressed = (Key.alt_l in self._pressed_keys or
                       Key.alt_r in self._pressed_keys)
        z_pressed = any(
            getattr(k, 'char', None) == 'z' or
            getattr(k, 'char', None) == '\x1a' or
            (hasattr(k, 'vk') and getattr(k, 'vk', None) == 0x5A)
            for k in self._pressed_keys
        )

        if alt_pressed and z_pressed:
            config.vietnamese_mode = not config.vietnamese_mode
            self.buffer.clear()
            self._pressed_keys.clear()
            if self._on_mode_change:
                self._on_mode_change()
            return True
        return False

    def _get_char(self, key):
        """Extract printable character from a key event."""
        if isinstance(key, KeyCode):
            if key.char is not None:
                if len(key.char) == 1 and ord(key.char) >= 32:
                    return key.char
        return None

    def _replace_keystroke(self, backspace_count, new_text):
        """Replace using backspace + keystroke simulation."""
        for _ in range(backspace_count):
            self.controller.press(Key.backspace)
            self.controller.release(Key.backspace)

        for ch in new_text:
            self.controller.type(ch)

"""Global keyboard hook for Vietnamese Telex input using pynput.

Uses a non-suppressed listener. Simulated events are tracked via a skip
counter so the hook ignores its own injected keystrokes.
"""

import threading
import winsound
from pynput import keyboard
from pynput.keyboard import Key, KeyCode, Controller

import config
import telex_engine
import vn_validator

# Map config modifier names to pynput Key sets
_MODIFIER_MAP = {
    'alt':        ({Key.alt_l, Key.alt_r},),
    'ctrl':       ({Key.ctrl_l, Key.ctrl_r},),
    'ctrl+alt':   ({Key.ctrl_l, Key.ctrl_r}, {Key.alt_l, Key.alt_r}),
    'ctrl+shift': ({Key.ctrl_l, Key.ctrl_r}, {Key.shift, Key.shift_r}),
}


class KeyboardHandler:
    def __init__(self, on_mode_change=None):
        self.controller = Controller()
        self.buffer = []
        self._skip_events = 0
        self._pressed_keys = set()
        self._on_mode_change = on_mode_change
        self._listener = None
        self._lock = threading.Lock()
        # Track last transform for retroactive undo
        self._last_transform = None  # {'key': str, 'old_buffer': list}
        # Save buffer on word-break so backspace can restore context
        self._committed_buffer = []

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
        total_bs = 0
        new_text = ''
        need_replace = False

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
                if key == Key.backspace:
                    if self.buffer:
                        self.buffer.pop()
                    elif self._committed_buffer:
                        # Backspace on empty buffer after word-break:
                        # user deleted the space, restore previous word context
                        self.buffer = self._committed_buffer[:]
                        self._committed_buffer = []
                elif key in (Key.enter, Key.tab, Key.space):
                    # Soft break: save buffer for possible restore
                    if self.buffer:
                        self._committed_buffer = self.buffer[:]
                    self.buffer.clear()
                    self._last_transform = None
                else:
                    if key not in (Key.shift, Key.shift_r, Key.ctrl_l, Key.ctrl_r,
                                   Key.alt_l, Key.alt_r, Key.alt_gr, Key.caps_lock,
                                   Key.cmd, Key.cmd_r):
                        # Hard break (arrows, escape, etc.): clear everything
                        self.buffer.clear()
                        self._committed_buffer = []
                        self._last_transform = None
                return

            # Word-break character
            if char in config.WORD_BREAK_CHARS:
                if self.buffer:
                    self._committed_buffer = self.buffer[:]
                self.buffer.clear()
                self._last_transform = None
                return

            # Not in Vietnamese mode: just track the buffer
            if not config.vietnamese_mode:
                self.buffer.append(char)
                return

            # Process through Telex engine
            old_buffer = self.buffer[:]
            new_buffer, backspace_count, transform_info = telex_engine.process_key(self.buffer, char)

            if backspace_count == 0:
                # No transform applied — check if appending this char
                # invalidates a previous transform (retroactive undo)
                self.buffer = new_buffer
                if self._last_transform and not vn_validator.is_valid_vietnamese(self.buffer):
                    # Revert: restore old buffer + literal key from that transform
                    reverted = self._last_transform['old_buffer'] + [self._last_transform['key']]
                    # Re-append any chars added after the transform (including current char)
                    transform_buf_len = len(self._last_transform['old_buffer'])
                    chars_after = self.buffer[transform_buf_len:]
                    reverted.extend(chars_after)
                    self._last_transform = None
                    self.buffer = reverted

                    # Erase what's on screen (old visible + the char that just passed through)
                    total_bs = len(old_buffer) + 1
                    new_text = ''.join(reverted)
                    self._skip_events = total_bs + len(new_text)
                    need_replace = True
                # If no retroactive undo needed, just fall through (need_replace stays False)
            else:
                # Transformation applied
                self.buffer = new_buffer
                self._last_transform = transform_info
                total_bs = backspace_count + 1

                diff_start = len(old_buffer) - backspace_count
                if diff_start < 0:
                    diff_start = 0
                new_text = ''.join(new_buffer[diff_start:])

                # Skip counter for our injected events
                self._skip_events = total_bs + len(new_text)
                need_replace = True

        # Release lock before sending keys
        if need_replace:
            self._replace_keystroke(total_bs, new_text)

    def _on_release(self, key):
        self._pressed_keys.discard(key)

    def _check_toggle(self):
        """Check if the configured switch key is pressed."""
        sk = config.switch_key
        modifier = sk.get('modifier', 'alt').lower()
        target_key = sk.get('key', 'z').lower()

        # Check modifier(s) are held
        mod_groups = _MODIFIER_MAP.get(modifier, ({Key.alt_l, Key.alt_r},))
        for group in mod_groups:
            if not any(k in self._pressed_keys for k in group):
                return False

        # Check the letter key
        target_vk = ord(target_key.upper())
        key_pressed = any(
            getattr(k, 'char', None) == target_key or
            getattr(k, 'char', '') == chr(ord(target_key) - 96) or  # ctrl+key control char
            (hasattr(k, 'vk') and getattr(k, 'vk', None) == target_vk)
            for k in self._pressed_keys
        )
        if not key_pressed:
            return False

        config.vietnamese_mode = not config.vietnamese_mode
        config.default_mode = config.vietnamese_mode
        self.buffer.clear()
        self._pressed_keys.clear()
        if config.beep_on_switch:
            freq = 800 if config.vietnamese_mode else 400
            threading.Thread(target=winsound.Beep, args=(freq, 80), daemon=True).start()
        if self._on_mode_change:
            self._on_mode_change()
        return True

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

"""Global keyboard hook for Vietnamese Telex input using pynput.

Uses a non-suppressed listener. Simulated events are detected via the
Windows LLKHF_INJECTED flag (passed by pynput as the ``injected``
parameter) so the hook ignores its own SendInput keystrokes.
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
        self._pressed_keys = set()
        self._on_mode_change = on_mode_change
        self._listener = None
        self._lock = threading.Lock()
        # Track last transform for retroactive undo
        self._last_transform = None  # {'key': str, 'old_buffer': list}
        # Buffer history stack for restoring context after word breaks
        self._buffer_history = []  # list of (buffer_snapshot, last_transform, raw_keystrokes)
        # Raw keystroke buffer: records original typed characters before transforms
        # Used to restore original keystrokes when word turns out to be non-Vietnamese
        self._raw_keystrokes = []
        # Whether any Telex transform was applied in the current word
        self._has_transforms = False

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

    def _on_press(self, key, injected=False):
        if injected:
            return

        total_bs = 0
        new_text = ''
        need_replace = False

        with self._lock:
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
                        old_buffer = self.buffer[:]
                        self.buffer.pop()
                        if self._raw_keystrokes:
                            self._raw_keystrokes.pop()
                        # Reposition tone if needed after deletion
                        reposition = self._reposition_tone_after_delete(old_buffer, self.buffer)
                        if reposition:
                            total_bs, new_text = reposition
                            need_replace = True
                    elif self._buffer_history:
                        # Backspace on empty buffer: user deleted back into
                        # the previous word — restore its context.
                        self.buffer, self._last_transform, self._raw_keystrokes, self._has_transforms = self._buffer_history.pop()
                elif key in (Key.enter, Key.tab, Key.space):
                    restore_result = self._check_and_restore()
                    if restore_result:
                        total_bs, new_text = restore_result
                        need_replace = True
                    self._push_history()
                    self._reset_word_state()
                else:
                    if key not in (Key.shift, Key.shift_r, Key.ctrl_l, Key.ctrl_r,
                                   Key.alt_l, Key.alt_r, Key.alt_gr, Key.caps_lock,
                                   Key.cmd, Key.cmd_r):
                        # Hard break (arrows, escape, etc.): clear everything
                        self._reset_word_state()
                        self._buffer_history.clear()
            elif char in config.WORD_BREAK_CHARS:
                # Word-break character: check restore before clearing
                restore_result = self._check_and_restore()
                if restore_result:
                    total_bs, new_text = restore_result
                    need_replace = True
                self._push_history()
                self._reset_word_state()
            elif not config.vietnamese_mode:
                # Not in Vietnamese mode: just track the buffer
                self.buffer.append(char)
                self._raw_keystrokes.append(char)
            else:
                # Vietnamese mode: process through Telex engine
                self._raw_keystrokes.append(char)
                old_buffer = self.buffer[:]
                new_buffer, backspace_count, transform_info = telex_engine.process_key(self.buffer, char)

                if backspace_count == 0:
                    # No transform — check retroactive undo
                    self.buffer = new_buffer
                    if self._last_transform and not vn_validator.is_valid_vietnamese(self.buffer):
                        reverted = self._last_transform['old_buffer'] + [self._last_transform['key']]
                        transform_buf_len = len(self._last_transform['old_buffer'])
                        chars_after = self.buffer[transform_buf_len:]
                        reverted.extend(chars_after)
                        self._last_transform = None
                        self.buffer = reverted

                        total_bs = len(old_buffer) + 1
                        new_text = ''.join(reverted)
                        need_replace = True
                else:
                    # Transformation applied
                    self.buffer = new_buffer
                    self._last_transform = transform_info
                    if transform_info is not None:
                        self._has_transforms = True
                    total_bs = backspace_count + 1

                    diff_start = len(old_buffer) - backspace_count
                    if diff_start < 0:
                        diff_start = 0
                    new_text = ''.join(new_buffer[diff_start:])
                    need_replace = True

        # Release lock before sending keys
        if need_replace:
            self._replace_keystroke(total_bs, new_text)

    def _on_release(self, key, injected=False):
        if injected:
            return
        self._pressed_keys.discard(key)

    def _push_history(self):
        """Save current buffer to history stack (if non-empty)."""
        if self.buffer:
            self._buffer_history.append((
                self.buffer[:], self._last_transform,
                self._raw_keystrokes[:], self._has_transforms,
            ))
            # Limit history depth
            if len(self._buffer_history) > 5:
                self._buffer_history.pop(0)

    def _reset_word_state(self):
        """Clear all per-word state for a new word."""
        self.buffer.clear()
        self._last_transform = None
        self._raw_keystrokes.clear()
        self._has_transforms = False

    def _check_and_restore(self):
        """Check if the current word is non-Vietnamese and should be restored.

        Returns (backspace_count, replacement_text) if restore is needed,
        or None if the word is valid Vietnamese / no transforms were applied.
        """
        if not config.vietnamese_mode:
            return None
        if not self.buffer or not self._has_transforms:
            return None

        # Check if the buffer already matches the raw keystrokes (no visible change)
        raw_text = ''.join(self._raw_keystrokes)
        current_text = ''.join(self.buffer)
        if raw_text == current_text:
            return None

        # Check if the completed word is a valid Vietnamese syllable
        if vn_validator.is_complete_vietnamese(self.buffer):
            return None

        # Not valid Vietnamese — restore original keystrokes
        backspace_count = len(current_text)
        return (backspace_count, raw_text)

    def _reposition_tone_after_delete(self, old_buffer, new_buffer):
        """Check if tone needs repositioning after a character was deleted.

        When deleting a final consonant or vowel, the tone position may shift.
        E.g., "toán" -> delete 'n' -> tone should move from 'a' to 'o' -> "tóa"

        Returns (backspace_count, replacement_text) or None.
        """
        if not config.vietnamese_mode or not new_buffer:
            return None

        # Find the current tone in the new buffer
        tone_idx = 0
        tone_pos = -1
        for i, ch in enumerate(new_buffer):
            info = telex_engine.get_base_and_tone(ch)
            if info and info[1] != 0:
                tone_idx = info[1]
                tone_pos = i
                break

        if tone_idx == 0:
            return None  # No tone to reposition

        # Find where tone SHOULD be in the new buffer
        correct_pos = telex_engine.find_tone_target(new_buffer)
        if correct_pos < 0 or correct_pos == tone_pos:
            return None  # Already correct

        # Move the tone: remove from old position, add at new position
        result = list(new_buffer)

        # Remove tone from current position
        old_info = telex_engine.get_base_and_tone(result[tone_pos])
        if old_info:
            result[tone_pos] = telex_engine.apply_tone(old_info[0], 0, old_info[2])

        # Add tone at correct position
        new_info = telex_engine.get_base_and_tone(result[correct_pos])
        if new_info:
            result[correct_pos] = telex_engine.apply_tone(new_info[0], tone_idx, new_info[2])

        self.buffer = result

        # The backspace for the deleted char already happened (the OS processes it).
        # We need to erase the remaining visible text and retype with repositioned tone.
        # After the OS backspace, len(new_buffer) chars are visible.
        return (len(new_buffer), ''.join(result))

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
        self._raw_keystrokes.clear()
        self._has_transforms = False
        self._last_transform = None
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

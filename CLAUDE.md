# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

MyVNKey is a Windows-only Vietnamese Unicode typing tool (like UniKey/OpenKey) using the Telex input method. It runs as a background app with a system tray icon, intercepts keystrokes globally, and transforms them into Vietnamese characters in real-time.

## Running

```
pip install -r requirements.txt
python main.py
```

No build step. No tests currently. The app requires Windows (uses Win32 APIs via ctypes and pynput).

## Architecture

The data flow is: **user keystroke** -> `keyboard_hook` -> `telex_engine` -> simulated backspace+retype -> **app receives Vietnamese text**.

### Threading Model

- **Main thread**: runs `pystray` system tray icon (blocking event loop)
- **Keyboard hook thread**: runs `pynput.keyboard.Listener` (blocking message loop)
- **App monitor thread**: polls foreground window every 200ms for per-app mode switching
- **Settings GUI**: tkinter runs in its own thread when opened from tray

### Key Module Relationships

- `main.py` — Entry point. Wires together all components, loads/saves config.
- `config.py` — Global mutable state (`vietnamese_mode`, `default_mode`, `app_rules`, settings) + JSON persistence to `~/.myvnkey.json`. All modules read/write this shared state directly.
- `telex_engine.py` — Pure function `process_key(buffer, key) -> (new_buffer, backspace_count)`. Stateless; all state is in the buffer passed in. This is the core logic for Vietnamese character composition.
- `keyboard_hook.py` — Non-suppressed pynput listener. Maintains a word buffer. When `telex_engine` returns a transform, it uses a **skip counter** (`_skip_events`) to ignore its own simulated keystrokes. The skip counter is critical — without it, injected backspaces corrupt the buffer.
- `app_monitor.py` — Uses ctypes (`GetForegroundWindow`, `QueryFullProcessImageNameW`, `GetWindowTextW`) to detect the active app. Matches against per-app rules (process name exact match, window title contains, or regex on title). Priority: regex > title > process.
- `tray_icon.py` — Generates icons programmatically with Pillow (green "V" / gray "E"). Exposes `update_icon()` called by both the keyboard hook and app monitor on mode changes.
- `settings_gui.py` — Tkinter window for managing per-app rules and general settings (switch key, beep, autorun).

### Critical Design Decisions

**Non-suppressed keyboard hook**: The listener does NOT suppress keystrokes. Characters pass through to the target app normally. When a Telex transform is needed, backspaces erase the already-typed characters and the replacement is typed via `controller.type()`. This avoids the deadlock that `suppress=True` causes on Windows.

**Skip counter for self-detection**: With a non-suppressed hook, injected keystrokes (backspaces + retyped chars) re-enter the hook. A counter (`_skip_events`) is set to the exact number of expected `on_press` events before injection. The hook decrements and skips these. This is fragile if the count is wrong — test carefully after any change to replacement logic.

**Clipboard mode was removed**: An earlier clipboard-based approach (Ctrl+V paste) was abandoned because `SendInput` events are queued during the hook callback on Windows, causing the clipboard to be restored before the paste executes. Only keystroke simulation mode is supported.

## Config File Format

`~/.myvnkey.json`:
```json
{
  "app_rules": [
    {"pattern": "Discord.exe", "match": "process", "vietnamese": true},
    {"pattern": "Signal", "match": "title", "vietnamese": false},
    {"pattern": "Slack|Teams", "match": "regex", "vietnamese": true}
  ],
  "default_mode": true,
  "beep_on_switch": false,
  "switch_key": {"modifier": "alt", "key": "z"},
  "autorun": false
}
```

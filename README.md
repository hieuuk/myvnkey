# MyVNKey

A lightweight Vietnamese typing tool for Windows, built for people who switch between multiple languages across different apps throughout the day. Instead of manually toggling your input method every time you switch windows, MyVNKey automatically activates the right language mode per application.

Using the **Telex** input method, it transforms keystrokes into Vietnamese characters in real-time — no separate IME or language pack needed.

## Why MyVNKey?

If you use Vietnamese in some apps (messaging, documents) but English in others (terminals, code editors, games), you know the pain of constantly toggling your input method. MyVNKey solves this with **per-app language rules** — set it once and forget it.

## Features

- **Per-app language switching** — the core feature. Automatically switch between Vietnamese and English based on the active application
  - Match by process name (exact), window title (contains), or regex
  - Detects PWAs in Chrome/Edge via window title matching
- **Telex input method** — type `aa` for `â`, `ow` for `ơ`, `dd` for `đ`, tone marks with `s/f/r/x/j/z`
- **Global keyboard hook** — works in any application
- **System tray icon** — shows current mode at a glance
- **Configurable hotkey** — default `Alt+Z` to toggle, customizable to any modifier+key combo
- **Settings GUI** — manage per-app rules, hotkey, beep, and autorun from the tray menu
- **Auto-run at startup** — optional Windows startup registration

## Download

Grab the latest release from the [Releases page](https://github.com/hieuuk/myvnkey/releases). Extract the zip and run `MyVNKey.exe` — no installation or Python required.

## Usage

The app starts in the system tray. Right-click the tray icon for:
- **Vietnamese Mode** — toggle on/off
- **Settings...** — open the settings window
- **Exit** — quit the app

### Running from source

Requires Windows 10/11 and Python 3.10+.

```bash
pip install -r requirements.txt
python main.py
```

### Telex Reference

| Input | Output | Description |
|-------|--------|-------------|
| `aa` | `â` | Circumflex A |
| `aw` | `ă` | Breve A |
| `ee` | `ê` | Circumflex E |
| `oo` | `ô` | Circumflex O |
| `ow` | `ơ` | Horn O |
| `uw` | `ư` | Horn U |
| `dd` | `đ` | Crossed D |
| `s` | sắc | Acute tone |
| `f` | huyền | Grave tone |
| `r` | hỏi | Hook above tone |
| `x` | ngã | Tilde tone |
| `j` | nặng | Dot below tone |
| `z` | — | Remove tone |

### Per-App Rules

Open **Settings** from the tray menu to add rules. Example setup:
- `Discord.exe` (Process Name) → Vietnamese
- `Signal` (Window Title) → English
- `Slack|Teams` (Regex) → Vietnamese

Apps not in the rule list use the last mode you set with the hotkey.

## Configuration

Settings are stored in `~/.myvnkey.json` and persist across restarts.

## License

MIT

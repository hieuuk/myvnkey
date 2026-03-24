# MyVNKey

A Vietnamese Unicode typing tool for Windows, similar to UniKey/OpenKey. Uses the **Telex** input method with real-time keystroke transformation.

## Features

- **Telex input method** — type `aa` for `â`, `ow` for `ơ`, `dd` for `đ`, tone marks with `s/f/r/x/j/z`
- **Global keyboard hook** — works in any application
- **System tray icon** — green "V" for Vietnamese, gray "E" for English
- **Configurable hotkey** — default `Alt+Z` to toggle, customizable to any modifier+key combo
- **Per-app language switching** — auto-switch Vietnamese/English based on the active application
  - Match by process name (exact), window title (contains), or regex
  - Detects PWAs in Chrome/Edge via window title matching
- **Settings GUI** — manage per-app rules, hotkey, beep, and autorun from the tray menu
- **Auto-run at startup** — optional Windows startup registration

## Requirements

- Windows 10/11
- Python 3.10+

## Installation

```bash
pip install -r requirements.txt
```

Dependencies: `pynput`, `pystray`, `Pillow`

## Usage

```bash
python main.py
```

The app starts in the system tray. Right-click the tray icon for:
- **Vietnamese Mode** — toggle on/off
- **Settings...** — open the settings window
- **Exit** — quit the app

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

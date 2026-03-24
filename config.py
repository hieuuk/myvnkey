"""Shared state, constants, and persistence for MyVNKey."""

import json
import os
import sys

# ── Config file path ─────────────────────────────────────────────────────────

CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.myvnkey.json')

# ── Mutable shared state ─────────────────────────────────────────────────────

vietnamese_mode = True       # Current active mode
default_mode = True          # Fallback mode (set by toggle key, used for unlisted apps)

# Per-app rules: list of {"pattern": str, "match": "process"|"title"|"regex", "vietnamese": bool}
app_rules = []

# ── Settings ─────────────────────────────────────────────────────────────────

beep_on_switch = False                          # Play a beep when language switches
switch_key = {'modifier': 'alt', 'key': 'z'}   # Hotkey to toggle Vietnamese mode
autorun = False                                 # Start with Windows

# ── Constants ────────────────────────────────────────────────────────────────

WORD_BREAK_CHARS = set(' \t\n\r,.;:!?/\\()[]{}<>@#$%^&*-+=~`\'"0123456789')

# Valid modifier + key options for the UI
MODIFIER_OPTIONS = ['Alt', 'Ctrl', 'Ctrl+Alt', 'Ctrl+Shift']
KEY_OPTIONS = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

# ── Persistence ──────────────────────────────────────────────────────────────


def load_config():
    """Load settings from the JSON config file."""
    global app_rules, default_mode, beep_on_switch, switch_key, autorun
    if not os.path.exists(CONFIG_FILE):
        return
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        raw_rules = data.get('app_rules', [])
        if isinstance(raw_rules, dict):
            app_rules = [
                {'pattern': k, 'match': 'process', 'vietnamese': v}
                for k, v in raw_rules.items()
            ]
        else:
            app_rules = raw_rules
        default_mode = data.get('default_mode', True)
        beep_on_switch = data.get('beep_on_switch', False)
        if 'switch_key' in data:
            switch_key = data['switch_key']
        autorun = data.get('autorun', False)
    except (json.JSONDecodeError, OSError):
        pass


def save_config():
    """Save settings to the JSON config file."""
    data = {
        'app_rules': app_rules,
        'default_mode': default_mode,
        'beep_on_switch': beep_on_switch,
        'switch_key': switch_key,
        'autorun': autorun,
    }
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


# ── Autorun (Windows registry) ──────────────────────────────────────────────

_REGISTRY_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'
_REGISTRY_NAME = 'MyVNKey'


def set_autorun(enabled):
    """Enable or disable auto-start with Windows via the registry."""
    global autorun
    autorun = enabled
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REGISTRY_KEY, 0,
                             winreg.KEY_SET_VALUE)
        if enabled:
            exe = sys.executable
            script = os.path.abspath(os.path.join(os.path.dirname(__file__), 'main.py'))
            winreg.SetValueEx(key, _REGISTRY_NAME, 0, winreg.REG_SZ,
                              f'"{exe}" "{script}"')
        else:
            try:
                winreg.DeleteValue(key, _REGISTRY_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception:
        pass

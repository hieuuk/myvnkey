"""System tray icon for MyVNKey."""

import os
import sys

import pystray
from PIL import Image

import config


def _get_asset_path(filename):
    """Get path to an asset file, works both in dev and PyInstaller builds."""
    if getattr(sys, '_MEIPASS', None):
        return os.path.join(sys._MEIPASS, 'assets', filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', filename)


def _load_icon(filename):
    """Load a tray icon from an asset PNG file."""
    return Image.open(_get_asset_path(filename))


class TrayIcon:
    def __init__(self, on_open_settings=None):
        self._icon_vn = _load_icon('v.png')
        self._icon_en = _load_icon('e.png')
        self._on_open_settings = on_open_settings
        self._tray = pystray.Icon(
            'myvnkey',
            icon=self._icon_vn if config.vietnamese_mode else self._icon_en,
            title=self._get_title(),
            menu=pystray.Menu(
                pystray.MenuItem(
                    'Vietnamese Mode',
                    self._toggle_vietnamese,
                    checked=lambda _: config.vietnamese_mode,
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem('Settings...', self._open_settings),
                pystray.MenuItem('Exit', self._exit),
            ),
        )

    def _get_title(self):
        mode = 'Vietnamese' if config.vietnamese_mode else 'English'
        return f'MyVNKey - {mode}'

    def _toggle_vietnamese(self, icon, item):
        config.vietnamese_mode = not config.vietnamese_mode
        self.update_icon()

    def _open_settings(self, icon, item):
        if self._on_open_settings:
            self._on_open_settings()

    def _exit(self, icon, item):
        self._tray.stop()

    def update_icon(self):
        """Update the tray icon to reflect current mode."""
        if config.vietnamese_mode:
            self._tray.icon = self._icon_vn
        else:
            self._tray.icon = self._icon_en
        self._tray.title = self._get_title()

    def run(self):
        """Run the tray icon (blocking, should be on main thread)."""
        self._tray.run()

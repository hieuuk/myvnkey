"""System tray icon for MyVNKey."""

import pystray
from PIL import Image, ImageDraw, ImageFont

import config


def _create_icon(letter, bg_color):
    """Generate a simple tray icon with a letter and background color."""
    size = 64
    img = Image.new('RGB', (size, size), bg_color)
    draw = ImageDraw.Draw(img)
    # Try to use a system font, fall back to default
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except (OSError, IOError):
        font = ImageFont.load_default()
    # Center the letter
    bbox = draw.textbbox((0, 0), letter, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) // 2
    y = (size - text_h) // 2 - bbox[1]
    draw.text((x, y), letter, fill='white', font=font)
    return img


class TrayIcon:
    def __init__(self):
        self._icon_vn = _create_icon('V', '#2E7D32')   # Green
        self._icon_en = _create_icon('E', '#757575')    # Gray
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
                pystray.MenuItem('Exit', self._exit),
            ),
        )

    def _get_title(self):
        mode = 'Vietnamese' if config.vietnamese_mode else 'English'
        return f'MyVNKey - {mode}'

    def _toggle_vietnamese(self, icon, item):
        config.vietnamese_mode = not config.vietnamese_mode
        self.update_icon()

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

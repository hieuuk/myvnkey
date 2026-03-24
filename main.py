"""MyVNKey - Vietnamese Unicode Typing Tool using Telex input method."""

import threading
import config
from keyboard_hook import KeyboardHandler
from tray_icon import TrayIcon
from app_monitor import AppMonitor
from settings_gui import open_settings


def main():
    config.load_config()

    tray = TrayIcon(on_open_settings=open_settings)
    handler = KeyboardHandler(on_mode_change=tray.update_icon)
    monitor = AppMonitor(on_mode_change=tray.update_icon)

    # Start keyboard listener in a daemon thread
    kb_thread = threading.Thread(target=handler.start, daemon=True)
    kb_thread.start()

    # Start foreground app monitor
    monitor.start()

    print("MyVNKey is running. Alt+Z to toggle Vietnamese/English mode.")
    print("Right-click the tray icon for options.")

    # Run tray on the main thread (pystray requires it)
    tray.run()

    # Clean up when tray exits
    monitor.stop()
    handler.stop()
    config.save_config()
    print("MyVNKey stopped.")


if __name__ == '__main__':
    main()

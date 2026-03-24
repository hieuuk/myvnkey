"""MyVNKey - Vietnamese Unicode Typing Tool using Telex input method."""

import threading
from keyboard_hook import KeyboardHandler
from tray_icon import TrayIcon


def main():
    tray = TrayIcon()
    handler = KeyboardHandler(on_mode_change=tray.update_icon)

    # Start keyboard listener in a daemon thread
    kb_thread = threading.Thread(target=handler.start, daemon=True)
    kb_thread.start()

    print("MyVNKey is running. Alt+Z to toggle Vietnamese/English mode.")
    print("Right-click the tray icon for options.")

    # Run tray on the main thread (pystray requires it)
    tray.run()

    # Clean up when tray exits
    handler.stop()
    print("MyVNKey stopped.")


if __name__ == '__main__':
    main()

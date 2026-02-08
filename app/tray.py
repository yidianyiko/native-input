"""System tray application."""

from typing import Optional

import pystray
from pystray import MenuItem as Item

from app.autostart import AutoStartManager
from app.config import APP_NAME, HOST, PORT
from app.icon import get_icon
from app.service import ServiceManager


class TrayApp:
    """System tray application for Agent Service."""

    def __init__(self):
        self.service = ServiceManager(host=HOST, port=PORT)
        self.autostart = AutoStartManager()
        self._icon: Optional[pystray.Icon] = None

    def _create_menu(self) -> pystray.Menu:
        """Create the tray menu."""
        return pystray.Menu(
            Item(
                f"状态: {'运行中' if self.service.is_running() else '已停止'}",
                None,
                enabled=False,
            ),
            Item(
                f"端口: {PORT}",
                None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            Item(
                "开机启动",
                self._toggle_autostart,
                checked=lambda item: self.autostart.is_enabled(),
            ),
            pystray.Menu.SEPARATOR,
            Item("退出", self._quit),
        )

    def _toggle_autostart(self, icon: pystray.Icon, item: Item) -> None:
        """Toggle auto-start setting."""
        if self.autostart.is_enabled():
            self.autostart.disable()
        else:
            self.autostart.enable()
        icon.update_menu()

    def _quit(self, icon: pystray.Icon, item: Item) -> None:
        """Quit the application."""
        self.service.stop()
        icon.stop()

    def run(self) -> None:
        """Run the tray application."""
        self.service.start()

        # Enable auto-start by default on first run
        if not self.autostart.is_enabled():
            self.autostart.enable()

        self._icon = pystray.Icon(
            APP_NAME,
            get_icon(),
            APP_NAME,
            menu=self._create_menu(),
        )

        self._icon.run()


def main() -> None:
    """Main entry point for the tray application."""
    TrayApp().run()


if __name__ == "__main__":
    main()

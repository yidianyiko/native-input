"""System tray application."""

import threading
from typing import Optional

import pystray
from pystray import MenuItem as Item

from app.autostart import AutoStartManager
from app.config import APP_NAME, HOST, PORT
from app.credentials import load_deepseek_api_key, save_deepseek_api_key
from app.icon import get_icon
from app.service import ServiceManager


class TrayApp:
    """System tray application for Agent Service."""

    def __init__(self):
        self.service = ServiceManager(host=HOST, port=PORT)
        self.autostart = AutoStartManager()
        self._icon: Optional[pystray.Icon] = None

    def _save_api_key(self, key: str) -> None:
        save_deepseek_api_key(key)
        if self._icon is not None:
            self._icon.update_menu()

    def _prompt_set_api_key(self, icon: pystray.Icon, item: Item) -> None:
        def _worker() -> None:
            # Lazy import: tkinter may not be present in all environments, and
            # importing it at module import time can break headless runs/tests.
            try:
                import tkinter as tk
                from tkinter import messagebox, simpledialog
            except Exception:
                return

            root = tk.Tk()
            root.withdraw()
            try:
                key = simpledialog.askstring(
                    "设置 API Key",
                    "请输入 DeepSeek API Key:",
                    show="*",
                    parent=root,
                )
                if key is None:
                    return
                key = key.strip()
                if not key:
                    messagebox.showerror("错误", "API Key 不能为空。", parent=root)
                    return
                self._save_api_key(key)
                messagebox.showinfo("成功", "API Key 已保存。", parent=root)
            finally:
                try:
                    root.destroy()
                except Exception:
                    pass

        threading.Thread(target=_worker, daemon=True).start()

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
            Item(
                f"Key: {'已配置' if load_deepseek_api_key() else '未配置'}",
                None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            Item("设置 API Key...", self._prompt_set_api_key),
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

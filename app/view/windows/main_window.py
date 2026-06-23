from __future__ import annotations

from qfluentwidgets import FluentWindow


class MainWindow(FluentWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

    def addUrls(self, urls: list[str]) -> None:
        pass

    def addTasks(self, tasks: list) -> None:
        pass

    def confirmPair(self, request) -> None:
        pass

    def alertException(self, message: str) -> None:
        pass

    def _setTheme(self, value) -> None:
        pass

    def _onSystemColorSchemeChanged(self, scheme) -> None:
        pass

    def _refreshBackgroundEffect(self) -> None:
        pass

    def _setBackgroundEffect(self, value) -> None:
        pass

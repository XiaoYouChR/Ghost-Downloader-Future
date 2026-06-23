from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget


class OptionCard(QWidget):
    optionsChanged = Signal()

    def options(self) -> dict:
        return {}


class OptionPanel(QWidget):
    optionsChanged = Signal()

    def options(self) -> dict:
        return {}


class UrlEditCard(OptionCard):
    def __init__(self, icon, title: str, parent=None, *, initial: str = ""):
        super().__init__(parent)


class HeadersEditCard(OptionCard):
    def __init__(self, icon, title: str, parent=None, *, initial: dict | None = None):
        super().__init__(parent)


class ProxiesEditCard(OptionCard):
    def __init__(self, icon, title: str, parent=None, *, initial: dict | None = None):
        super().__init__(parent)


class ClientProfileEditCard(OptionCard):
    def __init__(self, icon, title: str, parent=None, *, initial: str = ""):
        super().__init__(parent)


class SelectFolderCard(OptionCard):
    def __init__(self, icon, title: str, parent=None, *, initial=None):
        super().__init__(parent)

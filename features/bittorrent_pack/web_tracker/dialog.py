from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget
from qfluentwidgets import MessageBoxBase


class WebTrackerSourceCard(QWidget):
    removed = Signal(object)

    def __init__(self, url: str, cachedCount: int | None = None, parent=None):
        super().__init__(parent)
        self._url = url

    @property
    def url(self) -> str:
        return self._url

    def setCachedCount(self, count: int | None): ...

    def _initWidget(self): ...
    def _initLayout(self): ...
    def _bind(self): ...


class WebTrackerDialog(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)

    def _initWidget(self): ...
    def _initLayout(self): ...
    def _bind(self): ...

    def validate(self) -> bool: ...
    def _addSourceCard(self, url: str): ...

from urllib.parse import urlparse

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication
from loguru import logger

SUPPORTED_SCHEMES = {"http", "https", "ftp", "ftps", "magnet"}


class ClipboardListener(QObject):
    urlsDetected = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._clipboard = None
        self._enabled = False
        self._lastUrls: tuple[str, ...] = ()

    def setEnabled(self, enabled: bool) -> None:
        if self._clipboard is None:
            self._clipboard = QApplication.clipboard()

        if enabled and not self._enabled:
            self._clipboard.dataChanged.connect(self._onDataChanged)
        elif not enabled and self._enabled:
            self._clipboard.dataChanged.disconnect(self._onDataChanged)
        self._enabled = enabled

    def _onDataChanged(self) -> None:
        if self._clipboard.ownsClipboard():
            return

        urls: list[str] = []
        for line in self._clipboard.text().splitlines():
            url = line.strip()
            if not url:
                continue
            try:
                parsed = urlparse(url)
            except ValueError:
                continue
            if parsed.scheme in SUPPORTED_SCHEMES and parsed.geturl() == url:
                urls.append(url)

        if not urls:
            return

        snapshot = tuple(urls)
        if snapshot == self._lastUrls:
            return
        self._lastUrls = snapshot

        self.urlsDetected.emit(urls)

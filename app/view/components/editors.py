from PySide6.QtCore import QSize
from PySide6.QtWidgets import QPlainTextEdit


class AutoSizingEdit(QPlainTextEdit):
    def __init__(self, parent=None, *, minimumVisibleLines: int = 3, maximumVisibleLines: int = 10):
        super().__init__(parent)

    def minimumSizeHint(self) -> QSize:
        pass

    def sizeHint(self) -> QSize:
        pass


def headersToText(headers: dict[str, str]) -> str:
    return "\n".join(f"{k}: {v}" for k, v in headers.items())


def headersFromText(text: str) -> dict[str, str]:
    headers = {}
    for line in text.strip().splitlines():
        name, _, value = line.partition(":")
        name = name.strip()
        value = value.strip()
        if name and value:
            headers[name] = value
    return headers

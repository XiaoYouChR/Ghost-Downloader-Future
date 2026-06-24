from PySide6.QtCore import QSize
from PySide6.QtWidgets import QPlainTextEdit, QSizePolicy


class AutoSizingEdit(QPlainTextEdit):
    def __init__(self, parent=None, *, minimumVisibleLines: int = 3, maximumVisibleLines: int = 10):
        super().__init__(parent)
        self._minimumVisibleLines = minimumVisibleLines
        self._maximumVisibleLines = maximumVisibleLines
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.document().blockCountChanged.connect(self.updateGeometry)

    def _sizeForLines(self, count: int) -> QSize:
        margins = self.contentsMargins()
        viewportMargins = self.viewportMargins()
        padding = (
            margins.top() + margins.bottom()
            + viewportMargins.top() + viewportMargins.bottom()
            + self.frameWidth() * 2
            + round(self.document().documentMargin() * 2)
        )
        width = super().sizeHint().width()
        height = padding + self.fontMetrics().lineSpacing() * count
        return QSize(width, height)

    def minimumSizeHint(self) -> QSize:
        return self._sizeForLines(min(self._minimumVisibleLines, self.document().blockCount()))

    def sizeHint(self) -> QSize:
        visible = min(self.document().blockCount(), self._maximumVisibleLines)
        return self._sizeForLines(visible).expandedTo(self.minimumSizeHint())


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

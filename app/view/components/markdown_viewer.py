from PySide6.QtWidgets import QTextBrowser


class MarkdownViewer(QTextBrowser):
    def __init__(self, parent=None, minimumVisibleLines: int = 5, maximumVisibleLines: int = 16):
        super().__init__(parent)

    def setMarkdown(self, text: str) -> None:
        pass

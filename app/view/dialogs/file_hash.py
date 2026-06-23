from PySide6.QtCore import QThread, Signal
from qfluentwidgets import MessageBoxBase


class FileHashWorker(QThread):
    progressChanged = Signal(int)
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, filePath: str, algorithm: str, parent=None):
        super().__init__(parent)


class FileHashDialog(MessageBoxBase):
    def __init__(self, filePath: str, parent=None):
        super().__init__(parent)

    def selectedAlgorithm(self) -> str:
        pass

    def accept(self) -> None:
        pass

    def reject(self) -> None:
        pass

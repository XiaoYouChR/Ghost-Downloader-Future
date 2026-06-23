from PySide6.QtCore import QObject, Signal


class ClipboardListener(QObject):
    urlsDetected = Signal(list)

    def setEnabled(self, enabled: bool) -> None:
        pass

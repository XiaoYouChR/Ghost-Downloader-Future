from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QApplication


class SingletonApplication(QApplication):
    def __init__(self, argv: list[str], key: str):
        super().__init__(argv)

    def exec(self) -> int:
        pass

    def quit(self) -> None:
        pass

    def event(self, e: QEvent) -> bool:
        pass

    def _lockSingleInstance(self) -> None:
        pass

    def _unlockSingleInstance(self) -> None:
        pass

    def _onInterrupt(self, signum, frame) -> None:
        pass

    def _registerDbusReceiver(self) -> None:
        pass

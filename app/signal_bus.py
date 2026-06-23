from PySide6.QtCore import QObject, Signal


class SignalBus(QObject):
    showMainWindow = Signal()
    openFileRequested = Signal(list)
    catchException = Signal(str)


signalBus = SignalBus()

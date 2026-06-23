from qfluentwidgets import MessageBoxBase


class PlanTaskDialog(MessageBoxBase):
    SHUTDOWN = 0
    RESTART = 1
    OPEN_FILE = 2

    def __init__(self, parent=None):
        super().__init__(parent)

    def selectedAction(self) -> int:
        pass

    def selectedFilePath(self) -> str:
        pass

    def validate(self) -> bool:
        pass

    def _bind(self) -> None:
        pass

    def _onActionChanged(self) -> None:
        pass

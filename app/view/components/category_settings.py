from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget
from qfluentwidgets import SettingCard


class CategoryRowWidget(QWidget):
    editRequested = Signal(str)
    removeRequested = Signal(str)

    def __init__(self, category: dict, parent=None):
        super().__init__(parent)


class CategoryRulesCard(SettingCard):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

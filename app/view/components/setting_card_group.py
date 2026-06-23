from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from qfluentwidgets import SettingCard


class CollapsibleSettingCardGroup(QWidget):
    orderChanged = Signal()

    def __init__(self, title: str, key: str, parent=None):
        super().__init__(parent)

    def addSettingCard(self, card: SettingCard) -> None:
        pass

    def addSettingCards(self, cards: list[SettingCard]) -> None:
        pass

    def _reorder(self, offset: int) -> None:
        pass

    def _siblings(self) -> list[CollapsibleSettingCardGroup]:
        pass

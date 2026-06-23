from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget
from qfluentwidgets import RoundMenu

if TYPE_CHECKING:
    from app.models.task import Task


class TaskCard(QWidget):
    selectionChanged = Signal(bool, bool)

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self._task = task

    def refresh(self) -> None:
        pass

    def setSelectionMode(self, enter: bool) -> None:
        pass

    def isChecked(self) -> bool:
        pass

    def setChecked(self, checked: bool) -> None:
        pass

    def buildContextMenu(self) -> RoundMenu | None:
        pass


class UniversalTaskCard(TaskCard):
    pass

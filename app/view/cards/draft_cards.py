from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

if TYPE_CHECKING:
    from app.models.task import Task


class DraftCard(QWidget):
    categoryPicked = Signal(str)
    editRequested = Signal()

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self._task = task

    @property
    def task(self) -> Task:
        return self._task

    def _onNameEdited(self) -> None:
        pass


class UniversalDraftCard(DraftCard):
    pass

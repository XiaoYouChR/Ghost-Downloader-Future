from __future__ import annotations

from typing import TYPE_CHECKING

from qfluentwidgets import MessageBoxBase

if TYPE_CHECKING:
    from app.models.task import Task


class EditTaskDialog(MessageBoxBase):
    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self._task = task


class DraftEditDialog(EditTaskDialog):
    def accept(self):
        pass


class LiveEditDialog(EditTaskDialog):
    def __init__(self, task: Task, parent=None):
        super().__init__(task, parent)
        self._pendingParseId: str = ""

    def accept(self):
        pass

    def reject(self):
        pass

    def _setInteractive(self, enabled: bool) -> None:
        pass

    def _onReparsed(self, newTask: Task, options: dict):
        pass

    def _onReparseFailed(self, error: str):
        pass

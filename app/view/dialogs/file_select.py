from __future__ import annotations

from typing import TYPE_CHECKING

from qfluentwidgets import MessageBoxBase

if TYPE_CHECKING:
    from app.models.task import Task


class FileSelectDialog(MessageBoxBase):
    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self._task = task

    def selectedIndexes(self) -> set[int]:
        pass

    def validate(self) -> bool:
        pass

    def _buildTypeMenu(self) -> None:
        pass

    def _categoryCounts(self) -> dict[str, int]:
        pass

    def _updateBranchCheckState(self) -> None:
        pass

    def _updateAncestorCheckStates(self) -> None:
        pass

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer
from qfluentwidgets import MessageBoxBase

if TYPE_CHECKING:
    from app.models.task import Task
    from app.services.task_draft import TaskDraft
    from app.view.cards.draft_cards import DraftCard


class TaskDraftDialog(MessageBoxBase):

    def __init__(self, draft: TaskDraft, parent=None):
        super().__init__(parent)
        self._draft = draft
        self._parseTimer = QTimer(self)
        self._cardByUrl: dict[str, DraftCard] = {}

    def showStandalone(self) -> None:
        pass

    def showMask(self) -> int:
        pass

    def addUrls(self, urls: list[str]) -> None:
        pass

    def addParsedTasks(self, tasks: list[Task]) -> None:
        pass

    def done(self, code: int) -> None:
        pass

    def validate(self) -> bool:
        pass

    def _onParseSucceeded(self, url: str, task: Task) -> None:
        pass

    def _onParseFailed(self, url: str, error: str) -> None:
        pass

    def _onItemsReordered(self) -> None:
        pass

    def _onCleared(self) -> None:
        pass

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from app.models.task import Task


@dataclass
class DraftItem:
    url: str
    parseId: str = ""
    task: Task | None = None


class TaskDraft(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

    parsingBusyChanged = Signal(bool)
    parseSucceeded = Signal(str, object)
    parseFailed = Signal(str, str)
    itemRemoved = Signal(str)
    itemsReordered = Signal()
    cleared = Signal()
    taskConfirmed = Signal(object)          # late task after accept → taskService.add

    def urls(self) -> list[str]:
        pass

    def taskByUrl(self, url: str) -> Task | None:
        pass

    def canAccept(self) -> bool:
        pass

    def setBaseOptions(self, options: dict) -> None:
        pass

    def setUrlCategory(self, url: str, categoryId: str) -> None:
        pass

    def setUrls(self, urls: list[str]) -> None:
        pass

    def addParsedTasks(self, tasks: list[Task]) -> list[str]:
        pass

    def accept(self) -> list[Task]:
        pass

    def clear(self) -> None:
        pass

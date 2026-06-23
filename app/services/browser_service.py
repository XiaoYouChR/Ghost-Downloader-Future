from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from app.models.task import Task, TaskOptions, ResourceTaskOptions


class BrowserService(QObject):
    pairRequested = Signal(object)
    taskDraftRequested = Signal(list)

    @property
    def token(self) -> str:
        pass

    def regenerateToken(self) -> str:
        pass

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def approvePair(self, session, requestId: str) -> None:
        pass

    def rejectPair(self, session, requestId: str) -> None:
        pass

    def _toTaskOptions(self, source: str, payload: dict, title: str) -> TaskOptions:
        pass

    def _toResourceTaskOptions(self, resource: dict) -> ResourceTaskOptions:
        pass

    def _toTaskSummary(self, task: Task) -> dict:
        pass


browserService = BrowserService()

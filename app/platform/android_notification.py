from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models import Task


def notify(channelId: str, channelName: str, notificationId: int,
           title: str, text: str, *, ongoing: bool, lowImportance: bool) -> None:
    pass


def notifyTaskCompleted(task: Task) -> None:
    pass


def requestNotificationPermission() -> None:
    pass

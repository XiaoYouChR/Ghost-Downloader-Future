from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QFileInfo, QStandardPaths, Qt
from PySide6.QtWidgets import QFileIconProvider
from loguru import logger

from app.platform.desktop import openFile

if TYPE_CHECKING:
    from app.models.task import Task
    from desktop_notifier import DesktopNotifier

ICON_PATH = Path(QStandardPaths.writableLocation(
    QStandardPaths.StandardLocation.TempLocation
)) / "gd_finished_icon.png"

notifier: DesktopNotifier | None = None


async def init() -> None:
    from desktop_notifier import DesktopNotifier as DN
    global notifier
    notifier = DN(app_name="Ghost Downloader")


def notifyTaskCompleted(task: Task) -> None:
    if notifier is None:
        return

    outputPath = task.outputPath
    if not outputPath:
        return

    parentFolder = str(Path(outputPath).parent)

    try:
        QFileIconProvider().icon(QFileInfo(outputPath)).pixmap(48, 48).scaled(
            128, 128,
            aspectMode=Qt.AspectRatioMode.KeepAspectRatio,
            mode=Qt.TransformationMode.SmoothTransformation,
        ).save(str(ICON_PATH), "PNG")
    except Exception:
        pass

    from desktop_notifier import Icon, Button
    from app.services.coroutine_runner import coroutineRunner

    coroutineRunner.submit(notifier.send(
        title="下载完成",
        message=task.name,
        buttons=[
            Button(title="打开文件", on_pressed=lambda: openFile(outputPath)),
            Button(title="打开目录", on_pressed=lambda: openFile(parentFolder)),
        ],
        on_clicked=lambda: openFile(outputPath),
        icon=Icon(path=ICON_PATH) if ICON_PATH.exists() else None,
    ))

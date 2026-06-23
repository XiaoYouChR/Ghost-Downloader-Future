from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer, Signal

from app.config.cfg import cfg

if TYPE_CHECKING:
    from app.models.task import Task


class TaskStore:
    def __init__(self):
        self._tasks: dict[str, Task] = {}

    def add(self, task: Task) -> None:
        pass

    def remove(self, taskId: str) -> Task | None:
        pass

    def taskById(self, taskId: str) -> Task | None:
        return self._tasks.get(taskId)

    @property
    def tasks(self) -> dict[str, Task]:
        return self._tasks

    def flush(self) -> None:
        pass

    def loadSaved(self) -> list[Task]:
        pass


class TaskQueue:
    def __init__(self):
        self._waiting: list[str] = []
        self._running: dict[str, str] = {}   # taskId -> workId

    def wait(self, taskId: str) -> None:
        """taskId 进入等待队列。"""

    def cancel(self, taskId: str) -> None:
        """取消 taskId 的等待或运行。"""

    def isRunning(self, taskId: str) -> bool:
        return taskId in self._running

    def isWaiting(self, taskId: str) -> bool:
        return taskId in self._waiting

    def runningCount(self) -> int:
        return len(self._running)

    def pump(self) -> None:
        """按槽位上限把等待任务派发为运行;溢出的运行任务回退等待。"""


class TaskService(QObject):
    taskAdded = Signal(object)
    taskRemoved = Signal(str)
    taskStarted = Signal(object)
    taskPaused = Signal(object)
    taskCompleted = Signal(object)
    taskFailed = Signal(object)
    tasksAllCompleted = Signal()
    speedChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._store = TaskStore()
        self._queue = TaskQueue()
        self._speed = 0
        self._speedTimer = QTimer(self)
        self._speedTimer.setInterval(1000)
        self._speedTimer.timeout.connect(self._emitSpeed)
        cfg.maxTaskNum.valueChanged.connect(self._pumpSoon)

    @property
    def tasks(self) -> dict[str, Task]:
        return self._store.tasks

    def taskById(self, taskId: str) -> Task | None:
        return self._store.taskById(taskId)

    def add(self, task: Task) -> None:
        pass

    def pause(self, task: Task) -> None:
        pass

    def delete(self, task: Task, shouldDeleteFiles: bool) -> None:
        pass

    def redownload(self, task: Task) -> None:
        pass

    def edit(self, task: Task, options: dict, newTask: Task | None = None) -> None:
        pass

    def setCategory(self, task: Task, categoryId: str) -> None:
        pass

    def startAll(self) -> None:
        for task in self._store.tasks.values():
            self.add(task)

    def pauseAll(self) -> None:
        for task in self._store.tasks.values():
            self.pause(task)

    def resumeSaved(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def flush(self) -> None:
        self._store.flush()

    def addSpeed(self, bytesCount: int) -> None:
        self._speed += bytesCount

    def _emitSpeed(self) -> None:
        self.speedChanged.emit(self._speed)
        self._speed = 0

    def _start(self, task: Task) -> None:
        pass

    def _cancelRun(self, task: Task) -> None:
        pass

    def _pumpSoon(self) -> None:
        pass

    def _onRunDone(self, task: Task) -> None:
        pass

    def _onRunFailed(self, task: Task) -> None:
        pass


taskService = TaskService()

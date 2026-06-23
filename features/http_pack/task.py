from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
import asyncio

from app.models.task import Task, TaskStep, TaskStatus


@dataclass(kw_only=True, eq=False)
class HttpTask(Task):
    packId: str = "http"
    supportsEdit = True


@dataclass(kw_only=True)
class HttpTaskStep(TaskStep):
    url: str = ""
    fileSize: int = 0
    headers: dict[str, str] = field(default_factory=dict)
    proxies: dict[str, str] = field(default_factory=dict)
    subworkerCount: int = 8
    supportsRange: bool = False
    accelerated: bool = False
    outputFile: str = ""
    subworkers: list[HttpSubworker] = field(default_factory=list, repr=False)

    @property
    def outputPath(self) -> str:
        if self.outputFile:
            return self.outputFile
        return str(self.task.outputFolder / self.task.name)

    async def run(self) -> None: ...

    def _hasProgress(self) -> bool: ...
    def _loadRecord(self) -> list[HttpSubworker]: ...
    def _buildSubworkers(self) -> list[HttpSubworker]: ...
    async def _supervise(self) -> None: ...
    async def _runSubworker(self, subworker: HttpSubworker, file) -> None: ...
    def _autoSpeedUp(self) -> None: ...
    def _reassignSubworker(self) -> None: ...
    def _deleteRecord(self) -> None: ...


@dataclass
class HttpSubworker:
    index: int
    start: int
    end: int
    receivedBytes: int = 0
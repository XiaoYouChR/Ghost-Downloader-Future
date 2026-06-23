from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.models.task import Task, TaskStep, TaskStatus, TaskFile


@dataclass
class FtpConnectionInfo:
    scheme: str
    host: str
    port: int
    username: str
    password: str
    sourcePath: str

    async def connect(self, proxies: dict | None = None) -> "aioftp.Client": ...


@dataclass(kw_only=True)
class FtpFile(TaskFile):
    remotePath: str


@dataclass(kw_only=True)
class FtpStep(TaskStep):
    fileIndex: int
    remotePath: str
    fileSize: int = 0
    supportsRange: bool = False
    accelerated: bool = False
    outputFile: str = ""

    @property
    def outputPath(self) -> str:
        if self.outputFile:
            return self.outputFile
        return str(self.task.outputFolder / self.task.name)

    async def run(self) -> None: ...


@dataclass(kw_only=True, eq=False)
class FtpTask(Task):
    packId: str = "ftp"
    connectionInfo: FtpConnectionInfo
    sourceType: str = "file"
    proxies: dict[str, str] | None = None
    subworkerCount: int = 8

    def pendingSteps(self):
        selected = [s for s in self.steps if self._isStepSelected(s)]
        return [s for s in selected if s.status != TaskStatus.COMPLETED]

    def currentSnapshot(self) -> tuple[float, int, int]:
        selected = [s for s in self.steps if self._isStepSelected(s)]
        if not selected:
            return 0.0, 0, 0
        progress = sum(s.progress for s in selected) / len(selected)
        speed = sum(s.speed for s in selected)
        receivedBytes = sum(s.receivedBytes for s in selected)
        return progress, speed, receivedBytes

    def deleteFiles(self): ...

    def _isStepSelected(self, step: FtpStep) -> bool:
        if not self.files:
            return True
        for file in self.files:
            if file.index == step.fileIndex:
                return file.selected
        return False


@dataclass
class FtpSubworker:
    index: int
    start: int
    end: int
    receivedBytes: int = 0

from __future__ import annotations

from dataclasses import dataclass

from app.models.task import TaskStep
from http_pack.task import HttpTaskStep


@dataclass(kw_only=True)
class FFmpegResourceStep(HttpTaskStep):
    role: str = ""
    extension: str = ""


@dataclass(kw_only=True)
class FFmpegStep(TaskStep):
    canPause = False

    videoExtension: str = ""
    audioExtension: str = ""
    shouldDeleteSource: bool = True

    @property
    def outputFile(self) -> str:
        name = self.task.name
        stem = name.rsplit(".", 1)[0] if "." in name else name
        return str(self.task.outputFolder / f"{stem}.mp4")

    async def run(self) -> None: ...

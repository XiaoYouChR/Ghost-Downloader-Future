from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from http_pack.task import HttpTaskStep
from ffmpeg_pack.task import FFmpegStep


def pageStem(taskName: str, pageSuffix: str) -> str:
    base = taskName[:-4] if taskName.lower().endswith(".mp4") else taskName
    return f"{base}{pageSuffix}" if pageSuffix else base


@dataclass(kw_only=True)
class BilibiliVideoStep(HttpTaskStep):
    pageIndex: int = 0
    pageSuffix: str = ""

    @property
    def outputPath(self) -> str:
        return str(self.task.outputFolder / f"{pageStem(self.task.name, self.pageSuffix)}.video.m4s")


@dataclass(kw_only=True)
class BilibiliAudioStep(HttpTaskStep):
    pageIndex: int = 0
    pageSuffix: str = ""

    @property
    def outputPath(self) -> str:
        return str(self.task.outputFolder / f"{pageStem(self.task.name, self.pageSuffix)}.audio.m4s")


@dataclass(kw_only=True)
class BilibiliMergeStep(FFmpegStep):
    pageIndex: int = 0
    pageSuffix: str = ""

    @property
    def outputFile(self) -> str:
        return str(self.task.outputFolder / f"{pageStem(self.task.name, self.pageSuffix)}.mp4")

    @property
    def _videoPath(self) -> Path:
        return self.task.outputFolder / f"{pageStem(self.task.name, self.pageSuffix)}.video.m4s"

    @property
    def _audioPath(self) -> Path:
        return self.task.outputFolder / f"{pageStem(self.task.name, self.pageSuffix)}.audio.m4s"

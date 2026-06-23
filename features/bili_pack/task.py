from __future__ import annotations

from dataclasses import dataclass

from http_pack.task import HttpTaskStep
from ffmpeg_pack.task import FFmpegStep


@dataclass(kw_only=True)
class BilibiliVideoStep(HttpTaskStep):
    pageIndex: int = 0
    pageSuffix: str = ""

    @property
    def outputFile(self) -> str: ...


@dataclass(kw_only=True)
class BilibiliAudioStep(HttpTaskStep):
    pageIndex: int = 0
    pageSuffix: str = ""

    @property
    def outputFile(self) -> str: ...


@dataclass(kw_only=True)
class BilibiliMergeStep(FFmpegStep):
    pageIndex: int = 0
    pageSuffix: str = ""

    @property
    def outputFile(self) -> str: ...

    @property
    def videoPath(self) -> str: ...

    @property
    def audioPath(self) -> str: ...

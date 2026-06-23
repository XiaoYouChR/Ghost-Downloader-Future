from __future__ import annotations

from dataclasses import dataclass, field

from app.models.task import Task, TaskStep


DEFAULT_VIDEO_FORMAT = "bv*+ba/b"
PROGRESS_TOKEN = "__GD3_PROGRESS__"
FINAL_FILE_TOKEN = "__GD3_FINAL__"
ERROR_HINTS: dict[str, str] = ...


@dataclass(kw_only=True, eq=False)
class YtDlpTask(Task):
    packId: str = "ytdlp"


@dataclass(kw_only=True)
class YtDlpTaskStep(TaskStep):
    videoFormat: str = DEFAULT_VIDEO_FORMAT
    headers: dict[str, str] = field(default_factory=dict)
    proxies: dict[str, str] = field(default_factory=dict)
    lastMessage: str = ""

    async def run(self) -> None: ...


@dataclass(kw_only=True)
class YtDlpInstallStep(TaskStep):
    canPause = False
    binaryPath: str = ""

    async def run(self) -> None: ...

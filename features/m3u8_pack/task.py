from __future__ import annotations

from dataclasses import dataclass, field
from app.models.task import Task, TaskStep, TaskStatus


@dataclass(kw_only=True, eq=False)
class M3U8Task(Task):
    packId: str = "m3u8"
    manifestType: str = "m3u8"
    isLive: bool = False
    streams: list[dict] = field(default_factory=list)


@dataclass(kw_only=True)
class M3U8TaskStep(TaskStep):
    headers: dict[str, str] = field(default_factory=dict)
    proxies: dict[str, str] = field(default_factory=dict)
    threadCount: int = 8
    retryCount: int = 3
    requestTimeout: int = 100
    autoSelect: bool = True
    concurrentDownload: bool = True
    appendUrlParams: bool = False
    binaryMerge: bool = False
    checkSegmentsCount: bool = True
    delAfterDone: bool = True
    outputFormat: str = "mp4"
    customMuxAfterDone: str = ""
    subtitleFormat: str = "SRT"
    selectVideo: str = ""
    selectAllAudioSubtitle: bool = True
    maxSpeed: int = -1
    speedUnit: str = "Mbps"
    adKeyword: str = ""
    noDateInfo: bool = False
    keepImageSegments: bool = False
    decryptionEngine: str = "FFmpeg"
    decryptionBinaryPath: str = ""
    mp4RealTimeDecryption: bool = True
    liveKeepSegments: bool = False
    livePipeMux: bool = False
    liveFixVtt: bool = False
    liveWaitTime: int = 0
    liveTakeCount: int = 0
    lastMessage: str = ""
    liveStatus: str = ""
    liveElapsed: int = 0
    liveTotal: int = 0
    actualExtension: str = ""

    async def run(self) -> None: ...

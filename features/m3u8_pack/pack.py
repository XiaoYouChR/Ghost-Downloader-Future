from __future__ import annotations

from urllib.parse import urlparse, parse_qs

from app.models.pack import FeaturePack, TaskParser, FileType
from app.models.task import Task, TaskOptions
from app.platform.filesystem import localFilePath
from .task import M3U8Task, M3U8TaskStep


RELEASE_TAG = "v0.5.1-beta"
RELEASE_API = f"https://api.github.com/repos/nilaoda/N_m3u8DL-RE/releases/tags/{RELEASE_TAG}"
RELEASE_HEADERS = {
    "accept": "application/vnd.github+json",
    "user-agent": ...,
}

MEDIA_SUFFIXES = {
    ".m3u8", ".m3u", ".mpd", ".mp4", ".mkv",
    ".ts", ".webm", ".m4a", ".m4v", ".vtt", ".srt",
}
MANIFEST_SUFFIXES = {".m3u8", ".m3u", ".mpd"}


class M3U8Parser(TaskParser):
    priority = 80

    def match(self, options: TaskOptions) -> bool:
        if localFilePath(options.url, MANIFEST_SUFFIXES) is not None:
            return True
        lowered = options.url.lower()
        return ".m3u" in lowered or ".mpd" in lowered

    async def parse(self, options: TaskOptions) -> Task: ...

    def _parseStreams(self, body: str, manifestType: str) -> list[dict]: ...


class M3U8Pack(FeaturePack):
    packId = "m3u8"

    def __init__(self):
        from .config import m3u8Config
        self.config = m3u8Config

    def parsers(self):
        return [M3U8Parser()]

    def taskCard(self, task, parent=None):
        from .cards import M3U8TaskCard, M3U8LiveTaskCard
        if getattr(task, "isLive", False):
            return M3U8LiveTaskCard(task, parent)
        return M3U8TaskCard(task, parent)

    def draftCard(self, task, parent=None):
        from .cards import M3U8DraftCard
        return M3U8DraftCard(task, parent)

    def fileTypes(self):
        return [
            FileType(
                extensions=(".m3u8", ".m3u"),
                displayName=self.tr("M3U8 播放列表"),
                mimeType="application/vnd.apple.mpegurl",
                icon="m3u8",
            ),
            FileType(
                extensions=(".mpd",),
                displayName=self.tr("DASH 清单"),
                mimeType="application/dash+xml",
                icon="m3u8",
            ),
        ]

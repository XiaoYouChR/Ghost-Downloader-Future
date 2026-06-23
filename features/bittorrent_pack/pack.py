from app.models.pack import FeaturePack, TaskParser, FileType
from app.models.task import Task, TaskOptions
from app.platform.filesystem import localFilePath

from .config import bittorrentConfig
from .session import btSession
from .web_tracker.service import trackerService


class TorrentParser(TaskParser):
    priority = 85

    def match(self, options: TaskOptions) -> bool:
        from urllib.parse import urlparse
        url = options.url.strip()
        if urlparse(url).scheme.lower() == "magnet":
            return True
        return localFilePath(url, {".torrent"}) is not None or url.lower().endswith(".torrent")

    async def parse(self, options: TaskOptions) -> Task: ...


class BitTorrentPack(FeaturePack):
    packId = "bt"
    config = bittorrentConfig

    def parsers(self):
        return [TorrentParser()]

    def taskCard(self, task, parent=None):
        from .cards import BTTaskCard
        return BTTaskCard(task, parent)

    def draftCard(self, task, parent=None):
        from .cards import BTDraftCard
        return BTDraftCard(task, parent)

    def fileTypes(self):
        return [
            FileType(
                extensions=(".torrent",),
                displayName=self.tr("BitTorrent 种子文件"),
                mimeType="application/x-bittorrent",
                icon="torrent",
            ),
        ]

    def start(self):
        from app.services.coroutine_runner import coroutineRunner
        if bittorrentConfig.enableWebTrackers.value and bittorrentConfig.autoRefreshWebTrackers.value:
            coroutineRunner.run(trackerService.refresh())

    def stop(self):
        from app.services.coroutine_runner import coroutineRunner
        coroutineRunner.run(btSession.close())
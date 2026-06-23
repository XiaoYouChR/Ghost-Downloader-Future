from urllib.parse import urlparse

from app.models.pack import FeaturePack, TaskParser
from app.models.task import Task, TaskOptions
from .account import bilibiliAccount
from .config import bilibiliConfig


class BilibiliParser(TaskParser):
    priority = 50

    def match(self, options: TaskOptions) -> bool:
        hostname = (urlparse(options.url).hostname or "").lower()
        return hostname == "bilibili.com" or hostname.endswith(".bilibili.com")

    async def parse(self, options: TaskOptions) -> Task: ...

    def _selectStream(self, streams: list[dict], quality: int | None = None) -> str: ...

    async def _fetchSize(self, client, url: str, headers: dict, proxies: dict) -> int: ...


class BilibiliPack(FeaturePack):
    packId = "bili"
    config = bilibiliConfig

    def parsers(self):
        return [BilibiliParser()]

    def start(self):
        bilibiliAccount.fetchAccountInfo()

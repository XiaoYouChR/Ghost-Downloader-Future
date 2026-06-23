from urllib.parse import urlparse

from app.models.pack import FeaturePack, TaskParser
from app.models.task import Task, TaskOptions


class FtpParser(TaskParser):
    priority = 40

    def match(self, options: TaskOptions) -> bool:
        return urlparse(options.url).scheme.lower() in {"ftp", "ftps"}

    async def parse(self, options: TaskOptions) -> Task: ...


class FtpPack(FeaturePack):
    packId = "ftp"

    def parsers(self):
        return [FtpParser()]

    def taskCard(self, task, parent=None):
        from .cards import FtpTaskCard
        return FtpTaskCard(task, parent)

    def draftCard(self, task, parent=None):
        from .cards import FtpDraftCard
        return FtpDraftCard(task, parent)

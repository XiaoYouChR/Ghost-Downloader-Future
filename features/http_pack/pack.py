from urllib.parse import urlparse

from app.models.pack import FeaturePack, TaskParser
from app.models.task import Task, TaskOptions
from .task import HttpTask, HttpTaskStep


class HttpParser(TaskParser):
    priority = 0

    def match(self, options: TaskOptions) -> bool:
        return urlparse(options.url).scheme.lower() in {"http", "https"}

    async def parse(self, options: TaskOptions) -> Task: ...


class HttpPack(FeaturePack):
    packId = "http"

    def parsers(self):
        return [HttpParser()]

    def taskCard(self, task, parent=None):
        from .cards import HttpTaskCard
        return HttpTaskCard(task, parent)

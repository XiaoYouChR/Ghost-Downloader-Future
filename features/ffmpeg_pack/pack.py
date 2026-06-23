from app.models.pack import FeaturePack, TaskParser
from app.models.task import MergeTaskOptions, Task, TaskOptions
from .config import ffmpegConfig


class MergeParser(TaskParser):
    priority = 60

    def match(self, options: TaskOptions) -> bool:
        return isinstance(options, MergeTaskOptions)

    async def parse(self, options: TaskOptions) -> Task: ...


class FFmpegPack(FeaturePack):
    packId = "ffmpeg"
    config = ffmpegConfig

    def parsers(self):
        return [MergeParser()]

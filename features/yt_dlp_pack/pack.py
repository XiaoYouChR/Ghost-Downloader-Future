from urllib.parse import urlparse

from app.models.pack import FeaturePack, TaskParser
from app.models.task import Task, TaskOptions
from .task import YtDlpTask, YtDlpTaskStep


YOUTUBE_HOSTS = ("youtube.com", "youtu.be")
RELEASE_API = "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"
RELEASE_HEADERS = {
    "accept": "application/vnd.github+json",
    "user-agent": ...,
}


class YouTubeParser(TaskParser):
    priority = 70

    def match(self, options: TaskOptions) -> bool:
        host = (urlparse(options.url).hostname or "").lower()
        return any(host == h or host.endswith(f".{h}") for h in YOUTUBE_HOSTS)

    async def parse(self, options: TaskOptions) -> Task: ...


class YouTubePack(FeaturePack):
    packId = "ytdlp"

    def __init__(self):
        from .config import ytDlpConfig
        self.config = ytDlpConfig

    def parsers(self):
        return [YouTubeParser()]

    def draftCard(self, task, parent=None):
        from .cards import YtDlpDraftCard
        return YtDlpDraftCard(task, parent)

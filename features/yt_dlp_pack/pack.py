from __future__ import annotations

import asyncio
from urllib.parse import urlparse

from app.models.pack import FeaturePack, TaskParser
from app.models.task import Task, TaskOptions, SpecialFileSize
from app.platform.filesystem import toSafeFilename
from .config import ytDlpConfig, ytDlpRuntime
from .task import DEFAULT_VIDEO_FORMAT, YtDlpTask, YtDlpTaskStep, toInt


YOUTUBE_HOSTS = ("youtube.com", "youtu.be")


class YouTubeParser(TaskParser):
    priority = 70

    def match(self, options: TaskOptions) -> bool:
        host = (urlparse(options.url).hostname or "").lower()
        return any(host == h or host.endswith(f".{h}") for h in YOUTUBE_HOSTS)

    async def parse(self, options: TaskOptions) -> Task:
        from app.config.cfg import proxy

        url = options.url.strip()
        headers = dict(options.headers)
        videoFormat = DEFAULT_VIDEO_FORMAT

        probedTitle = ""
        probedSize = SpecialFileSize.UNKNOWN

        execPath = ytDlpRuntime.path()
        if execPath:
            args = [
                url, "-f", videoFormat, "--no-playlist", "--skip-download", "--no-warnings",
                "--print", "%(title)s", "--print", "%(filesize_approx)s",
            ]
            proxyUrl = proxy()
            if proxyUrl:
                args.extend(["--proxy", proxyUrl])
            for name, value in headers.items():
                text = str(value).strip()
                if text:
                    args.extend(["--add-header", f"{name}:{text}"])

            try:
                process = await asyncio.create_subprocess_exec(
                    execPath, *args,
                    stdin=asyncio.subprocess.DEVNULL,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                stdout, _ = await asyncio.wait_for(process.communicate(), timeout=20)
                if process.returncode == 0:
                    lines = stdout.decode("utf-8", errors="ignore").strip().splitlines()
                    probedTitle = lines[0].strip() if lines else ""
                    probedSize = toInt(lines[1]) if len(lines) > 1 else SpecialFileSize.UNKNOWN
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
            except OSError:
                pass

        name = toSafeFilename(probedTitle) if probedTitle else "YouTube 视频"

        task = YtDlpTask(
            name=f"{name}.mp4",
            url=url,
            fileSize=probedSize,
            outputFolder=options.outputFolder,
        )
        task.addStep(YtDlpTaskStep(
            stepIndex=1,
            videoFormat=videoFormat,
            headers=headers,
        ))
        return task


class YouTubePack(FeaturePack):
    packId = "ytdlp"

    def __init__(self):
        self.config = ytDlpConfig

    def parsers(self):
        return [YouTubeParser()]

    def draftCard(self, task, parent=None):
        from .cards import YtDlpDraftCard
        return YtDlpDraftCard(task, parent)

    def optionCards(self, task, parent=None):
        from app.view.components.option_cards import OutputFolderCard
        return [
            OutputFolderCard(parent, initial=task.outputFolder),
        ]

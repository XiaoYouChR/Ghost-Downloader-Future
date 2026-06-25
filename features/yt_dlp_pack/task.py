from __future__ import annotations

import asyncio
import sys
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path

from app.models.task import Task, TaskStep, TaskStatus
from app.platform.filesystem import toPosixPath
from .config import ytDlpRuntime

DEFAULT_VIDEO_FORMAT = "bv*+ba/b"
PROGRESS_TOKEN = "__GD3_PROGRESS__"
FINAL_FILE_TOKEN = "__GD3_FINAL__"
PROGRESS_TEMPLATE = (
    f"download:{PROGRESS_TOKEN}"
    "%(progress.downloaded_bytes)s|%(progress.total_bytes)s|"
    "%(progress.total_bytes_estimate)s|%(progress.speed)s"
)
FINAL_TEMPLATE = f"after_move:{FINAL_FILE_TOKEN}%(filepath)s"

ERROR_HINTS = (
    ("is not available in your country", "该视频在当前地区不可用，可在设置里配置代理后重试"),
    ("video unavailable", "视频不可用（可能已被删除或设为私有）"),
    ("private video", "私有视频，需要有权限账号的 cookies"),
    ("members-only", "会员专享视频，需要对应会员账号的 cookies"),
    ("confirm your age", "年龄限制视频，需要登录账号的 cookies"),
    ("confirm you're not a bot", "YouTube 要求人机验证，请在设置里配置 cookies"),
    ("requested format is not available", "请求的画质不可用，请改用其它格式"),
    ("http error 403", "下载被拒绝（403），链接可能已过期，请重试"),
)


def toInt(value: str) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


@dataclass(kw_only=True, eq=False)
class YtDlpTask(Task):
    packId: str = "ytdlp"


@dataclass(kw_only=True)
class YtDlpTaskStep(TaskStep):
    videoFormat: str = DEFAULT_VIDEO_FORMAT
    headers: dict[str, str] = field(default_factory=dict)
    lastMessage: str = ""

    @property
    def _outputTemplate(self) -> str:
        return toPosixPath(self.task.outputFolder / "%(title)s.%(ext)s")

    def _buildCommand(self) -> list[str]:
        from ffmpeg_pack.config import ffmpegRuntime

        args = [
            self.task.url,
            "-f", self.videoFormat,
            "-o", self._outputTemplate,
            "--no-playlist",
            "--newline",
            "--no-color",
            "--no-simulate",
            "--progress",
            "--progress-template", PROGRESS_TEMPLATE,
            "--print", FINAL_TEMPLATE,
        ]
        ffmpegPath = ffmpegRuntime.path()
        if ffmpegPath:
            args.extend(["--ffmpeg-location", ffmpegPath])
        from app.config.cfg import proxyUrl
        proxy = proxyUrl()
        if proxy:
            args.extend(["--proxy", proxy])
        for name, value in self.headers.items():
            text = value.strip()
            if text:
                args.extend(["--add-header", f"{name}:{text}"])
        return args

    def _parseOutputLine(self, line: str):
        text = line.strip()
        if not text:
            return
        if text.startswith(FINAL_FILE_TOKEN):
            self._finalPath = text[len(FINAL_FILE_TOKEN):].strip()
            return
        if text.startswith(PROGRESS_TOKEN):
            parts = text[len(PROGRESS_TOKEN):].split("|")
            if len(parts) >= 4:
                downloaded = toInt(parts[0])
                total = toInt(parts[1]) or toInt(parts[2])
                self.receivedBytes = downloaded
                self.speed = toInt(parts[3])
                if total > 0:
                    self.task.fileSize = max(self.task.fileSize, total)
                    self.progress = min(99.5, downloaded / total * 100)
            return
        self.lastMessage = text[:1000]

    async def _readOutput(self, stream: asyncio.StreamReader):
        buffer = ""
        while True:
            chunk = await stream.read(4096)
            if not chunk:
                break
            buffer += chunk.decode("utf-8", errors="ignore")
            buffer = buffer.replace("\r\n", "\n").replace("\r", "\n")
            lines = buffer.split("\n")
            buffer = lines.pop()
            for line in lines:
                self._parseOutputLine(line)
        if buffer.strip():
            self._parseOutputLine(buffer)

    async def run(self) -> None:

        execPath = ytDlpRuntime.path()
        if not execPath:
            raise RuntimeError("未找到可用的 yt-dlp，请先在设置中安装或配置运行时")

        self._finalPath = ""
        self.task.outputFolder.mkdir(parents=True, exist_ok=True)

        process = await asyncio.create_subprocess_exec(
            execPath,
            *self._buildCommand(),
            cwd=Path(execPath).parent,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        readerTask = asyncio.create_task(self._readOutput(process.stdout))

        try:
            await process.wait()
            await readerTask

            if process.returncode != 0:
                lowered = self.lastMessage.lower()
                hint = next((h for needle, h in ERROR_HINTS if needle in lowered), "")
                raise RuntimeError(hint or self.lastMessage or f"yt-dlp 退出码异常: {process.returncode}")

            if self._finalPath:
                path = Path(self._finalPath)
                if path.is_file() and path.stat().st_size > 0:
                    self.task.fileSize = max(self.task.fileSize, path.stat().st_size)
                    if path.name != self.task.name:
                        self.task.setName(path.name)

            self.setStatus(TaskStatus.COMPLETED)
        except asyncio.CancelledError:
            if process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=3)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
            if not readerTask.done():
                readerTask.cancel()
                with suppress(asyncio.CancelledError):
                    await readerTask
            self.setStatus(TaskStatus.PAUSED)
            raise


@dataclass(kw_only=True)
class YtDlpInstallStep(TaskStep):
    canPause = False
    binaryPath: str = ""

    async def run(self) -> None:
        path = Path(self.binaryPath)
        if not path.is_file():
            raise FileNotFoundError(f"未找到已下载的 yt-dlp: {path}")
        if sys.platform != "win32":
            path.chmod(path.stat().st_mode | 0o755)
        self.setStatus(TaskStatus.COMPLETED)

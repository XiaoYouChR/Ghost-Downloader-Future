from pathlib import Path

from qfluentwidgets import ConfigItem, FolderValidator

from app.config.paths import APP_DATA_DIR
from app.models.pack import BinaryRuntime, PackConfig
from app.models.task import Task
from app.platform.filesystem import findExecutable


class YtDlpRuntime(BinaryRuntime):
    name = "yt-dlp"

    def binaryPath(self) -> str:
        return findExecutable(Path(ytDlpConfig.installFolder.value), "yt-dlp")

    async def installTask(self) -> Task: ...


class YtDlpConfig(PackConfig):
    installFolder = ConfigItem("YtDlp", "InstallFolder", f"{APP_DATA_DIR}/YtDlp", FolderValidator())

    def setupSettings(self, settingPage): ...


ytDlpRuntime = YtDlpRuntime()
ytDlpConfig = YtDlpConfig()

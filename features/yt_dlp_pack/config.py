import platform
import sys
from pathlib import Path

from qfluentwidgets import ConfigItem, FolderValidator

from app.client import buildClient
from app.config.cfg import cfg
from app.config.paths import APP_DATA_DIR
from app.models.pack import BinaryRuntime, PackConfig
from app.models.task import Task
from app.platform.android import IS_ANDROID
from app.platform.filesystem import findExecutable, toPosixPath

RELEASE_API = "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"


class YtDlpConfig(PackConfig):
    installFolder = ConfigItem("YtDlp", "InstallFolder", f"{APP_DATA_DIR}/YtDlp", FolderValidator())

    def setupSettings(self, settingPage):
        from app.view.components.setting_card_group import CollapsibleSettingCardGroup
        from app.view.components.setting_cards import SelectFolderSettingCard, RuntimeCard

        self.group = CollapsibleSettingCardGroup(self.tr("YouTube 下载"), "ytdlp", settingPage.container)
        self.installFolderCard = SelectFolderSettingCard(
            ytDlpConfig.installFolder, f"{APP_DATA_DIR}/YtDlp",
            self.tr("yt-dlp 安装目录"),
            self.group,
        )
        self.runtimeCard = RuntimeCard(ytDlpRuntime, self.group)

        self.installFolderCard.pathChanged.connect(lambda _: self.runtimeCard.refreshStatus())
        self.group.addSettingCards([self.installFolderCard, self.runtimeCard])
        settingPage.addSettingGroup(self.group)
        self.runtimeCard.refreshStatus()


ytDlpConfig = YtDlpConfig()


class YtDlpRuntime(BinaryRuntime):
    name = "yt-dlp"
    canInstall = not IS_ANDROID

    def path(self) -> str:
        return findExecutable(Path(ytDlpConfig.installFolder.value), "yt-dlp")

    async def installTask(self) -> Task:
        from features.http_pack.task import HttpTaskStep
        from disk_pack.task import InstallTask
        from .task import YtDlpInstallStep

        machine = platform.machine().lower()
        if sys.platform == "win32":
            assetName = "yt-dlp.exe"
        elif sys.platform == "darwin":
            assetName = "yt-dlp_macos"
        elif machine in {"arm64", "aarch64"}:
            assetName = "yt-dlp_linux_aarch64"
        else:
            assetName = "yt-dlp_linux"

        client = buildClient(headers={"accept": "application/vnd.github+json"})
        try:
            response = await client.get(RELEASE_API)
            response.raise_for_status()
            release = await response.json()
        finally:
            client.close()

        assets = release.get("assets")
        if not isinstance(assets, list):
            raise RuntimeError("GitHub Release 返回了无效的 assets 数据")

        asset = next((item for item in assets if item.get("name") == assetName), None)
        if asset is None:
            raise RuntimeError(f"未找到适用于当前平台的 yt-dlp 安装包: {assetName}")

        downloadUrl = asset["browser_download_url"].strip()
        fileSize = asset["size"]
        if not downloadUrl or fileSize <= 0:
            raise RuntimeError("GitHub Release 返回了不完整的安装包信息")

        installFolder = Path(ytDlpConfig.installFolder.value)
        binaryName = "yt-dlp.exe" if sys.platform == "win32" else "yt-dlp"
        binaryPath = toPosixPath(installFolder / binaryName)

        task = InstallTask(
            name=f"yt-dlp 安装 ({assetName})",
            url=downloadUrl,
            packId="ytdlp",
            fileSize=fileSize,
            outputFolder=installFolder,
            installFolder=str(installFolder),
        )
        task.addStep(HttpTaskStep(
            stepIndex=1,
            url=downloadUrl,
            fileSize=fileSize,
            headers=dict(cfg.defaultRequestHeaders.value),
            subworkerCount=cfg.preBlockNum.value,
            canUseRangeRequests=True,
            outputFile=binaryPath,
        ))
        task.addStep(YtDlpInstallStep(
            stepIndex=2,
            binaryPath=binaryPath,
        ))
        return task


ytDlpRuntime = YtDlpRuntime()

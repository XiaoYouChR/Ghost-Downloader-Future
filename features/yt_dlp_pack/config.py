from __future__ import annotations

import platform
import sys
from pathlib import Path

from PySide6.QtWidgets import QWidget
from qfluentwidgets import BoolValidator, ConfigItem, FolderValidator, OptionsConfigItem, OptionsValidator, RangeConfigItem, RangeValidator

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
    parallelFragments = RangeConfigItem("YtDlp", "ParallelFragments", 4, RangeValidator(1, 16))
    loginBrowser = OptionsConfigItem(
        "YtDlp", "LoginBrowser", "",
        OptionsValidator(["", "chrome", "firefox", "edge", "safari"]),
    )
    shouldPreferMp4 = ConfigItem("YtDlp", "PreferMp4", True, BoolValidator())
    subtitleLanguages = ConfigItem("YtDlp", "SubtitleLanguages", "en")
    shouldEmbedThumbnail = ConfigItem("YtDlp", "EmbedThumbnail", True, BoolValidator())
    shouldEmbedChapters = ConfigItem("YtDlp", "EmbedChapters", True, BoolValidator())
    shouldEmbedMetadata = ConfigItem("YtDlp", "EmbedMetadata", True, BoolValidator())

    def settingGroups(self, parent: QWidget) -> list:
        from qfluentwidgets import ComboBoxSettingCard, FluentIcon, SwitchSettingCard
        from app.view.components.setting_card_group import CollapsibleSettingCardGroup
        from app.view.components.setting_cards import SelectFolderSettingCard, RuntimeCard, SpinBoxSettingCard

        group = CollapsibleSettingCardGroup(self.tr("YouTube 下载"), "ytdlp", parent)
        installFolderCard = SelectFolderSettingCard(
            ytDlpConfig.installFolder, f"{APP_DATA_DIR}/YtDlp",
            self.tr("yt-dlp 安装目录"),
            group,
        )
        runtimeCard = RuntimeCard(ytDlpRuntime, group)
        installFolderCard.pathChanged.connect(runtimeCard._onInstallFolderChanged)

        group.addSettingCards([
            installFolderCard,
            runtimeCard,
            SpinBoxSettingCard(
                FluentIcon.SPEED_HIGH,
                self.tr("并行分片数"),
                self.tr("同时下载的视频分片数量，越高越快但可能被限流"),
                configItem=self.parallelFragments,
                parent=group,
            ),
            ComboBoxSettingCard(
                self.loginBrowser,
                FluentIcon.PEOPLE,
                self.tr("登录浏览器"),
                self.tr("从指定浏览器读取 YouTube 登录状态，用于下载需要登录的内容"),
                texts=[self.tr("不使用"), "Chrome", "Firefox", "Edge", "Safari"],
                parent=group,
            ),
            SwitchSettingCard(
                FluentIcon.VIDEO,
                self.tr("优先 MP4 格式"),
                self.tr("优先选择 H.264/MP4 编码，避免输出 WebM/MKV"),
                self.shouldPreferMp4,
                group,
            ),
            SwitchSettingCard(
                FluentIcon.PHOTO,
                self.tr("嵌入缩略图"),
                self.tr("下载完成后通过 FFmpeg 将封面嵌入文件"),
                self.shouldEmbedThumbnail,
                group,
            ),
            SwitchSettingCard(
                FluentIcon.BOOK_SHELF,
                self.tr("嵌入章节"),
                self.tr("下载完成后通过 FFmpeg 将章节标记嵌入文件"),
                self.shouldEmbedChapters,
                group,
            ),
            SwitchSettingCard(
                FluentIcon.INFO,
                self.tr("嵌入元数据"),
                self.tr("下载完成后通过 FFmpeg 将标题、作者等信息嵌入文件"),
                self.shouldEmbedMetadata,
                group,
            ),
        ])
        runtimeCard.refreshStatus()
        return [group]


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

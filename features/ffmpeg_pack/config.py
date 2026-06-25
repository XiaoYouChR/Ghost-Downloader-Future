import asyncio
import platform
import sys
from pathlib import Path

from app.client import buildClient
from app.config.cfg import ConfigItem
from app.config.paths import APP_DATA_DIR
from app.models.pack import BinaryRuntime, PackConfig
from app.models.task import Task
from app.platform.android import IS_ANDROID, nativeLibraryDir
from app.platform.filesystem import findExecutable
from app.view.components.setting_cards import RuntimeCard


RELEASE_API = "https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest"


class FFmpegConfig(PackConfig):
    installFolder = ConfigItem("FFmpeg", "InstallFolder", f"{APP_DATA_DIR}/FFmpeg")

    def setupSettings(self, settingPage):
        from app.view.components.setting_card_group import CollapsibleSettingCardGroup
        from app.view.components.setting_cards import SelectFolderSettingCard

        self.ffmpegGroup = CollapsibleSettingCardGroup(self.tr("FFmpeg"), "ffmpeg", settingPage.container)
        self.installFolderCard = SelectFolderSettingCard(
            ffmpegConfig.installFolder, f"{APP_DATA_DIR}/FFmpeg",
            self.tr("FFmpeg 安装目录"), self.tr("选择 FFmpeg 安装目录"),
            self.ffmpegGroup,
        )
        self.runtimeCard = FFmpegRuntimeCard(self.ffmpegGroup)

        self.installFolderCard.pathChanged.connect(lambda _: self.runtimeCard.refreshStatus())
        self.ffmpegGroup.addSettingCards([self.installFolderCard, self.runtimeCard])
        settingPage.addSettingGroup(self.ffmpegGroup)
        self.runtimeCard.refreshStatus()


ffmpegConfig = FFmpegConfig()


class FFmpegRuntime(BinaryRuntime):
    name = "FFmpeg"

    def path(self) -> str:
        if IS_ANDROID:
            nativeDir = nativeLibraryDir()
            if not nativeDir:
                return ""
            binary = Path(nativeDir) / "libffmpeg.so"
            return str(binary) if binary.exists() else ""
        return findExecutable(Path(ffmpegConfig.installFolder.value), "ffmpeg", "bin")

    def ffprobePath(self) -> str:
        if IS_ANDROID:
            nativeDir = nativeLibraryDir()
            if not nativeDir:
                return ""
            binary = Path(nativeDir) / "libffprobe.so"
            return str(binary) if binary.exists() else ""
        return findExecutable(Path(ffmpegConfig.installFolder.value), "ffprobe", "bin")

    async def probeVersion(self) -> str:
        path = self.path()
        if not path:
            return ""
        process = await asyncio.create_subprocess_exec(
            path, "-version",
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await process.communicate()
        if process.returncode != 0:
            return ""
        line = stdout.decode("utf-8", errors="ignore").splitlines()[0].strip()
        return line.removeprefix("ffmpeg version ").split(" Copyright", 1)[0].strip() or line

    async def installTask(self) -> Task:
        if sys.platform != "win32":
            raise RuntimeError("一键安装 FFmpeg 仅支持 Windows 平台")

        machine = platform.machine().lower()
        if machine in {"amd64", "x86_64"}:
            target = "win64"
        elif machine in {"arm64", "aarch64"}:
            target = "winarm64"
        else:
            raise RuntimeError(f"不支持的 Windows 架构: {platform.machine()}")

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

        bestScore = -1
        bestAsset = None
        for asset in assets:
            lowerName = asset["name"].lower()
            if target not in lowerName or not lowerName.endswith(".zip") or "shared" in lowerName:
                continue
            score = 0
            if "master-latest" in lowerName:
                score += 100
            if "-gpl" in lowerName:
                score += 10
            if "-latest-" in lowerName:
                score += 5
            if score > bestScore:
                bestScore = score
                bestAsset = asset

        if bestAsset is None:
            raise RuntimeError(f"未找到适用于当前平台的 FFmpeg 安装包: {target}")

        url = bestAsset["browser_download_url"].strip()
        fileName = bestAsset["name"].strip()
        fileSize = bestAsset["size"]
        if not url or not fileName or fileSize <= 0:
            raise RuntimeError("GitHub Release 返回了不完整的 FFmpeg 安装包信息")

        from features.disk_pack.pack import buildBinaryInstallTask

        ffmpegName = "ffmpeg.exe"
        ffprobeName = "ffprobe.exe"
        return buildBinaryInstallTask(
            "ffmpeg",
            Path(ffmpegConfig.installFolder.value),
            [ffmpegName, ffprobeName],
            url=url,
            fileName=fileName,
            fileSize=fileSize,
            name=f"FFmpeg 安装 ({machine})",
        )


class FFmpegRuntimeCard(RuntimeCard):
    def _initWidget(self):
        super()._initWidget()
        if IS_ANDROID:
            self.installButton.hide()
        elif sys.platform == "win32":
            self.installButton.setText(self.tr("一键安装"))
        elif sys.platform == "darwin":
            self.installButton.setText(self.tr("复制安装命令"))
        else:
            self.installButton.setText(self.tr("复制安装命令"))


ffmpegRuntime = FFmpegRuntime()

import sys
from pathlib import Path

from app.config.cfg import ConfigItem
from app.config.paths import APP_DATA_DIR
from app.models.pack import BinaryRuntime, PackConfig
from app.models.task import Task
from app.platform.android import IS_ANDROID, nativeLibraryDir
from app.platform.filesystem import findExecutable
from app.view.components.setting_cards import RuntimeCard


class FFmpegRuntime(BinaryRuntime):
    name = "FFmpeg"

    def binaryPath(self) -> str:
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

    async def probeVersion(self) -> str: ...

    async def installTask(self) -> Task: ...


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


class FFmpegConfig(PackConfig):
    installFolder = ConfigItem("FFmpeg", "InstallFolder", f"{APP_DATA_DIR}/FFmpeg")

    def setupSettings(self, settingPage): ...


ffmpegRuntime = FFmpegRuntime()
ffmpegConfig = FFmpegConfig()

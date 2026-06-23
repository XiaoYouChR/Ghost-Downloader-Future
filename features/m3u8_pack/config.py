from pathlib import Path

from qfluentwidgets import (
    BoolValidator,
    ConfigItem,
    FolderValidator,
    OptionsConfigItem,
    OptionsValidator,
    RangeConfigItem,
    RangeValidator,
)

from app.config.cfg import cfg
from app.config.paths import APP_DATA_DIR
from app.models.pack import BinaryRuntime, PackConfig
from app.models.task import Task
from app.platform.android import IS_ANDROID, nativeLibraryDir
from app.platform.filesystem import findExecutable


class M3U8Runtime(BinaryRuntime):
    name = "N_m3u8DL-RE"

    def binaryPath(self) -> str:
        if IS_ANDROID:
            nativeDir = nativeLibraryDir()
            if not nativeDir:
                return ""
            binary = Path(nativeDir) / "libnm3u8dlre.so"
            return str(binary) if binary.exists() else ""
        return findExecutable(Path(m3u8Config.installFolder.value), "N_m3u8DL-RE")

    async def installTask(self) -> Task: ...


class M3U8Config(PackConfig):
    installFolder = ConfigItem("M3U8", "InstallFolder", f"{APP_DATA_DIR}/M3U8DL", FolderValidator())
    associateFileTypes = ConfigItem("M3U8", "AssociateFileTypes", False, BoolValidator())
    outputFormat = OptionsConfigItem("M3U8", "OutputFormat", "mp4", OptionsValidator(["mp4", "mkv"]))
    threadCount = RangeConfigItem("M3U8", "ThreadCount", 8, RangeValidator(1, 64))
    retryCount = RangeConfigItem("M3U8", "RetryCount", 3, RangeValidator(0, 20))
    requestTimeout = RangeConfigItem("M3U8", "RequestTimeout", 100, RangeValidator(5, 600))
    autoSelect = ConfigItem("M3U8", "AutoSelect", True, BoolValidator())
    concurrentDownload = ConfigItem("M3U8", "ConcurrentDownload", True, BoolValidator())
    appendUrlParams = ConfigItem("M3U8", "AppendUrlParams", False, BoolValidator())
    binaryMerge = ConfigItem("M3U8", "BinaryMerge", False, BoolValidator())
    checkSegmentsCount = ConfigItem("M3U8", "CheckSegmentsCount", True, BoolValidator())
    liveKeepSegments = ConfigItem("M3U8", "LiveKeepSegments", False, BoolValidator())
    livePipeMux = ConfigItem("M3U8", "LivePipeMux", False, BoolValidator())
    liveFixVtt = ConfigItem("M3U8", "LiveFixVtt", False, BoolValidator())
    liveWaitTime = RangeConfigItem("M3U8", "LiveWaitTime", 0, RangeValidator(0, 100000))
    liveTakeCount = RangeConfigItem("M3U8", "LiveTakeCount", 0, RangeValidator(0, 1000))
    decryptionEngine = OptionsConfigItem(
        "M3U8", "DecryptionEngine", "FFmpeg",
        OptionsValidator(["FFmpeg", "MP4Decrypt", "Shaka Packager"]),
    )
    decryptionBinaryPath = ConfigItem("M3U8", "DecryptionBinaryPath", "")
    mp4RealTimeDecryption = ConfigItem("M3U8", "MP4RealTimeDecryption", True, BoolValidator())
    maxSpeed = RangeConfigItem("M3U8", "MaxSpeed", -1, RangeValidator(-1, 1000000))
    speedUnit = OptionsConfigItem("M3U8", "SpeedUnit", "Mbps", OptionsValidator(["Mbps", "Kbps"]))
    adKeyword = ConfigItem("M3U8", "AdKeyword", "")
    subtitleFormat = OptionsConfigItem("M3U8", "SubtitleFormat", "SRT", OptionsValidator(["SRT", "VTT"]))
    noDateInfo = ConfigItem("M3U8", "NoDateInfo", False, BoolValidator())
    keepImageSegments = ConfigItem("M3U8", "KeepImageSegments", False, BoolValidator())
    delAfterDone = ConfigItem("M3U8", "DelAfterDone", True, BoolValidator())
    customMuxAfterDone = ConfigItem("M3U8", "CustomMuxAfterDone", "")
    selectAllAudioSubtitle = ConfigItem("M3U8", "SelectAllAudioSubtitle", True, BoolValidator())

    def setupSettings(self, settingPage): ...


m3u8Runtime = M3U8Runtime()
m3u8Config = M3U8Config()

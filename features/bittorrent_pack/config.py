from app.config.cfg import ConfigItem
from app.models.pack import PackConfig
from qfluentwidgets import BoolValidator, RangeConfigItem, RangeValidator


class BitTorrentConfig(PackConfig):
    enableDht = ConfigItem("BitTorrent", "EnableDHT", True, BoolValidator())
    enableLsd = ConfigItem("BitTorrent", "EnableLSD", True, BoolValidator())
    enablePex = ConfigItem("BitTorrent", "EnablePEX", True, BoolValidator())
    enableWebTrackers = ConfigItem("BitTorrent", "EnableWebTrackers", True, BoolValidator())
    autoRefreshWebTrackers = ConfigItem("BitTorrent", "AutoRefreshWebTrackers", True, BoolValidator())
    saveMagnetFile = ConfigItem("BitTorrent", "SaveMagnetTorrentFile", False, BoolValidator())
    seedingRatioLimit = RangeConfigItem("BitTorrent", "SeedingRatioLimit", 100, RangeValidator(0, 10000))
    seedingTimeLimit = RangeConfigItem("BitTorrent", "SeedingTimeLimit", 0, RangeValidator(0, 100000))
    maxConnections = RangeConfigItem("BitTorrent", "MaxConnections", 200, RangeValidator(0, 10000))
    maxUploadSpeed = RangeConfigItem("BitTorrent", "MaxUploadSpeed", 0, RangeValidator(0, 1000000))
    listenPort = RangeConfigItem("BitTorrent", "ListenPort", 6881, RangeValidator(1024, 65535))
    proxyPeer = ConfigItem("BitTorrent", "ProxyPeer", False, BoolValidator())
    anonymousMode = ConfigItem("BitTorrent", "AnonymousMode", False, BoolValidator())
    enableIpFilter = ConfigItem("BitTorrent", "EnableIpFilter", False, BoolValidator())
    ipFilterPath = ConfigItem("BitTorrent", "IpFilterPath", "")
    userAgent = ConfigItem("BitTorrent", "UserAgent", "")
    diskCacheSize = RangeConfigItem("BitTorrent", "DiskCacheSize", 64, RangeValidator(1, 4096))
    enableSuperSeeding = ConfigItem("BitTorrent", "EnableSuperSeeding", False, BoolValidator())
    enableSequentialDownload = ConfigItem("BitTorrent", "EnableSequentialDownload", False, BoolValidator())

    def setupSettings(self, settingPage): ...


bittorrentConfig = BitTorrentConfig()

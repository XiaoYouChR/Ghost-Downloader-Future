import asyncio
from urllib.parse import urlsplit

from PySide6.QtCore import QObject, Signal

from app.config.cfg import cfg, proxies

from .config import bittorrentConfig


class BTSession(QObject):
    alertReceived = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._session = None
        self._supervisor = None

    def open(self):
        if self._session is not None:
            return
        import libtorrent as lt
        from app.config.constants import VERSION
        self._session = lt.session({
            "user_agent": f"GhostDownloader/{VERSION} libtorrent/{lt.__version__}",
            "listen_interfaces": f"0.0.0.0:{bittorrentConfig.listenPort.value}",
            "connections_limit": bittorrentConfig.maxConnections.value,
            "download_rate_limit": self._downloadLimit(),
            "upload_rate_limit": bittorrentConfig.maxUploadSpeed.value,
            "enable_dht": bittorrentConfig.enableDht.value,
            "enable_lsd": bittorrentConfig.enableLsd.value,
            "announce_to_all_trackers": True,
            "announce_to_all_tiers": True,
            "alert_mask": lt.alert.category_t.all_categories,
            **self._toProxySettings(proxies()),
        })
        for item in (
            bittorrentConfig.maxUploadSpeed,
            bittorrentConfig.maxConnections,
            cfg.isSpeedLimitEnabled,
            cfg.speedLimitation,
        ):
            item.valueChanged.connect(self._onLimitChanged)
        self._supervisor = asyncio.get_running_loop().create_task(self._supervise())

    async def close(self):
        if self._supervisor is not None:
            self._supervisor.cancel()
            try:
                await self._supervisor
            except asyncio.CancelledError:
                pass
            self._supervisor = None
        self._session = None

    def session(self):
        return self._session

    def _onLimitChanged(self, _value=None):
        if self._session is None:
            return
        self._session.apply_settings({
            "download_rate_limit": self._downloadLimit(),
            "upload_rate_limit": bittorrentConfig.maxUploadSpeed.value,
            "connections_limit": bittorrentConfig.maxConnections.value,
        })

    def _downloadLimit(self) -> int:
        if not cfg.isSpeedLimitEnabled.value:
            return 0
        return cfg.speedLimitation.value

    def _toProxySettings(self, currentProxies: dict | None) -> dict:
        if not currentProxies:
            return {}
        proxyUrl = str(currentProxies.get("https") or currentProxies.get("http") or "").strip()
        if not proxyUrl:
            return {}
        parsed = urlsplit(proxyUrl)
        import libtorrent as lt
        if parsed.scheme.lower() != "socks5" or not parsed.hostname or not parsed.port:
            return {}
        hasCredentials = bool(parsed.username or parsed.password)
        return {
            "proxy_type": lt.proxy_type_t.socks5_pw if hasCredentials else lt.proxy_type_t.socks5,
            "proxy_hostname": parsed.hostname,
            "proxy_port": parsed.port,
            "proxy_username": parsed.username or "",
            "proxy_password": parsed.password or "",
            "proxy_hostnames": True,
            "proxy_peer_connections": True,
            "proxy_tracker_connections": True,
            "force_proxy": False,
        }

    async def _supervise(self):
        while self._session is not None:
            for alert in self._session.pop_alerts():
                self.alertReceived.emit(alert)
            await asyncio.sleep(1)


btSession = BTSession()

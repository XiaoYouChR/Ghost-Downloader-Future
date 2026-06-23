REASON_DOWNLOAD = "download"
REASON_BROWSER = "browser"


class BackgroundKeepAlive:
    def __init__(self):
        self._activeReasons: set[str] = set()
        self._running = False
        self._speed = 0
        self._wakeLock = None

    def holdFor(self, reason: str) -> None:
        self._activeReasons.add(reason)
        if reason == REASON_DOWNLOAD:
            self._setWakeLock(True)
        self._updateService()

    def release(self, reason: str) -> None:
        self._activeReasons.discard(reason)
        if reason == REASON_DOWNLOAD:
            self._setWakeLock(False)
        self._updateService()

    def setSpeed(self, speed: int) -> None:
        self._speed = speed
        if self._running:
            self._updateService()

    def _setWakeLock(self, active: bool) -> None:
        pass

    def _updateService(self) -> None:
        pass

    def _startService(self, statusMessage: str) -> None:
        pass

    def _stopService(self) -> None:
        pass


keepAlive = BackgroundKeepAlive()


def requestIgnoreBatteryOptimizations() -> None:
    pass

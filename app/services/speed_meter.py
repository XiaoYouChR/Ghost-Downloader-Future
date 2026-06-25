from __future__ import annotations

import asyncio

from PySide6.QtCore import QObject, QTimer, Signal

from app.config.cfg import cfg


class SpeedMeter(QObject):
    speedChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bytes = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

    def addSpeed(self, byteCount: int) -> None:
        self._bytes += byteCount
        if not self._timer.isActive():
            self._timer.start()

    async def waitForSpeedLimit(self) -> None:
        while cfg.isSpeedLimitEnabled.value and self._bytes > cfg.speedLimitation.value:
            await asyncio.sleep(0.1)

    def _tick(self) -> None:
        self.speedChanged.emit(self._bytes)
        idle = self._bytes == 0
        self._bytes = 0
        if idle:
            self._timer.stop()


speedMeter = SpeedMeter()

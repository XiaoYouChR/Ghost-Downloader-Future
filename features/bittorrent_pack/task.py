from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from app.models.task import Task, TaskStep, TaskFile


@dataclass(kw_only=True, eq=False)
class BTTask(Task):
    packId: str = "bt"
    sourceType: str = "torrent"
    torrentData: str = ""
    resumeData: str = ""
    trackers: list[str] = field(default_factory=list)
    shareRatioPercent: int = 0
    seedingTimeSeconds: int = 0
    isSeeding: bool = False
    stateText: str = ""
    peerCount: int = 0
    seedCount: int = 0
    downloadRate: int = 0
    uploadRate: int = 0

    @property
    def step(self) -> TaskStep:
        return self.steps[0]

    async def run(self): ...

    async def _supervise(self): ...

    def _onAlert(self, alert): ...

    async def _saveResume(self): ...

    def _isSeedingLimitReached(self) -> bool: ...

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

RELEASE_API = "https://api.github.com/repos/XiaoYouChR/Ghost-Downloader-3/releases/latest"


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    size: int
    downloadCount: int
    downloadUrl: str


@dataclass(frozen=True)
class Release:
    version: str
    publishedAt: str
    body: str
    pageUrl: str
    prerelease: bool
    assets: list[ReleaseAsset]


def _parseRelease(data: dict) -> Release:
    pass


async def fetchRelease() -> Release:
    pass


def isOutdated(release: Release) -> bool:
    pass


def bestAsset(release: Release) -> ReleaseAsset | None:
    pass

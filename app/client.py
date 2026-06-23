from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wreq import Client, Emulation

FALLBACK_PROFILE = "chrome"


def toEmulation(profile: str, sourceUa: str) -> Emulation | None:
    pass


def buildClient(
    proxies: dict | None = None,
    *,
    emulation: Emulation | None = None,
    headers: dict | None = None,
    timeout: int | None = None,
) -> Client:
    pass


def profileFamilies() -> list[str]:
    pass


def profileVersions(family: str) -> list[str]:
    pass

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.pack import FeaturePack


@dataclass(frozen=True)
class PackManifest:
    name: str
    entryPath: Path
    directory: Path
    dependencies: tuple[str, ...]


def loadPacks(featuresDir: Path) -> list[FeaturePack]:
    manifests = [m for m in (_manifestOf(p) for p in featuresDir.iterdir() if p.is_dir()) if m]
    ordered = _orderedByDependency(manifests)
    return [pack for m in ordered if (pack := _loadManifest(m)) is not None]


def _manifestOf(packDir: Path) -> PackManifest | None:
    pass


def _orderedByDependency(manifests: list[PackManifest]) -> list[PackManifest]:
    pass


def _loadManifest(manifest: PackManifest) -> FeaturePack | None:
    pass

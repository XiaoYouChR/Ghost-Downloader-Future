from __future__ import annotations

from typing import TYPE_CHECKING

from qfluentwidgets import MessageBoxBase

if TYPE_CHECKING:
    from app.update import Release, ReleaseAsset


class ReleaseInfoDialog(MessageBoxBase):
    def __init__(self, release: Release, parent=None):
        super().__init__(parent)

    def selectedAsset(self) -> ReleaseAsset | None:
        pass

    def validate(self) -> bool:
        pass

from __future__ import annotations

from qfluentwidgets import MessageBoxBase


class CategoryEditDialog(MessageBoxBase):
    def __init__(self, parent=None, *, category=None):
        super().__init__(parent)

    def category(self) -> dict | None:
        pass

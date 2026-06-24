from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QHBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel, FluentIcon, TransparentToolButton, ToolTipFilter, isDarkTheme,
)

from app.format import toReadableSize

if TYPE_CHECKING:
    from app.models.task import Task


class DraftCard(QWidget):
    categoryPicked = Signal(str)
    editRequested = Signal()

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self._task = task

        self.nameLabel = BodyLabel(task.name, self)
        self.sizeLabel = BodyLabel(toReadableSize(task.fileSize) if task.fileSize > 0 else "", self)
        self.editButton = TransparentToolButton(FluentIcon.EDIT, self)

        self.setFixedHeight(35)
        self.editButton.setFixedSize(28, 28)
        self.editButton.setToolTip(self.tr("编辑任务参数"))
        self.editButton.installEventFilter(ToolTipFilter(self.editButton))
        self.editButton.setVisible(task.canEdit)
        self.editButton.clicked.connect(self.editRequested.emit)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 8, 0)
        layout.addWidget(self.nameLabel, 1)
        layout.addWidget(self.sizeLabel)
        layout.addWidget(self.editButton)

    @property
    def task(self) -> Task:
        return self._task

    def _onNameEdited(self) -> None:
        self.nameLabel.setText(self._task.name)

    def paintEvent(self, e) -> None:
        painter = QPainter(self)
        painter.setPen(QColor(0, 0, 0, 96 if isDarkTheme() else 24))
        painter.drawLine(self.rect().topLeft(), self.rect().topRight())


class UniversalDraftCard(DraftCard):
    pass

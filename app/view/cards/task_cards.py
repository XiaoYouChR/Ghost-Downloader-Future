from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QApplication
from qfluentwidgets import (
    BodyLabel, CardWidget, CheckBox, FluentIcon, ProgressBar,
    RoundMenu, Action, isDarkTheme, themeColor,
)

from app.format import toReadableSize, toReadableTime
from app.models.task import TaskStatus
from app.platform.desktop import openFile
from app.services.task_service import taskService

if TYPE_CHECKING:
    from app.models.task import Task


class TaskCard(QWidget):
    selectionChanged = Signal(bool, bool)

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self._task = task
        self._selectionMode = False

        self.checkBox = CheckBox(self)
        self.checkBox.setFixedSize(23, 23)
        self.checkBox.setVisible(False)
        self.checkBox.clicked.connect(lambda checked: self.selectionChanged.emit(checked, False))

    def refresh(self) -> None:
        pass

    def setSelectionMode(self, enter: bool) -> None:
        self._selectionMode = enter
        self.checkBox.setVisible(enter)
        if not enter:
            self.checkBox.setChecked(False)

    def isChecked(self) -> bool:
        return self.checkBox.isChecked()

    def setChecked(self, checked: bool) -> None:
        if checked != self.isChecked():
            self.checkBox.setChecked(checked)

    def buildContextMenu(self) -> RoundMenu | None:
        menu = RoundMenu(parent=self)

        copyUrl = Action(FluentIcon.COPY, self.tr("复制下载链接"), self)
        copyUrl.triggered.connect(lambda: QApplication.clipboard().setText(self._task.url))
        menu.addAction(copyUrl)

        redownload = Action(FluentIcon.UPDATE, self.tr("重新下载"), self)
        redownload.triggered.connect(lambda: taskService.redownload(self._task))
        menu.addAction(redownload)

        return menu

    def mouseReleaseEvent(self, e) -> None:
        super().mouseReleaseEvent(e)
        if e.button() == Qt.MouseButton.LeftButton:
            extend = bool(e.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            checked = True if extend or not self._selectionMode else not self.isChecked()
            self.selectionChanged.emit(checked, extend)

    def mouseDoubleClickEvent(self, e) -> None:
        super().mouseDoubleClickEvent(e)
        if e.button() == Qt.MouseButton.LeftButton:
            openFile(self._task.outputPath)

    def contextMenuEvent(self, e) -> None:
        menu = self.buildContextMenu()
        if menu:
            menu.exec(e.globalPos())
            e.accept()


class UniversalTaskCard(TaskCard):

    def __init__(self, task: Task, parent=None):
        super().__init__(task, parent)
        self.setFixedHeight(60)

        self.nameLabel = BodyLabel(task.name, self)
        self.statusLabel = BodyLabel("", self)
        self.progressBar = ProgressBar(self)

        self.progressBar.setFixedHeight(3)
        self.statusLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        infoLayout = QHBoxLayout()
        infoLayout.addWidget(self.nameLabel, 1)
        infoLayout.addWidget(self.statusLabel)

        contentLayout = QVBoxLayout()
        contentLayout.setContentsMargins(0, 0, 0, 0)
        contentLayout.setSpacing(4)
        contentLayout.addLayout(infoLayout)
        contentLayout.addWidget(self.progressBar)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.addWidget(self.checkBox)
        layout.addLayout(contentLayout, 1)

        self.refresh()

    def refresh(self) -> None:
        task = self._task
        progress, speed, receivedBytes = task.currentSnapshot()
        self.progressBar.setValue(int(progress))

        if task.status == TaskStatus.RUNNING:
            parts = [toReadableSize(speed) + "/s"]
            if task.fileSize > 0:
                parts.append(f"{toReadableSize(receivedBytes)} / {toReadableSize(task.fileSize)}")
            self.statusLabel.setText("  ".join(parts))
        elif task.status == TaskStatus.COMPLETED:
            self.statusLabel.setText(self.tr("已完成"))
        elif task.status == TaskStatus.FAILED:
            self.statusLabel.setText(task.lastError or self.tr("失败"))
        elif task.status == TaskStatus.PAUSED:
            self.statusLabel.setText(self.tr("已暂停"))
        elif task.status == TaskStatus.WAITING:
            self.statusLabel.setText(self.tr("等待中"))

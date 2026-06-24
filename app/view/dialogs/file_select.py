from __future__ import annotations

from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QSignalBlocker
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView, QFileIconProvider, QHBoxLayout,
    QHeaderView, QWidget,
)
from qfluentwidgets import (
    BodyLabel, MessageBoxBase, PrimaryPushButton,
    PushButton, SubtitleLabel,
)

from app.format import toReadableSize
from app.view.components.tree_view import AutoSizingTreeView

if TYPE_CHECKING:
    from app.models.task import Task


class FileSelectDialog(MessageBoxBase):

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self._task = task
        self._fileItems: dict[int, QStandardItem] = {}

        self.titleLabel = SubtitleLabel(self.tr("选择下载文件"), self)
        self.summaryLabel = BodyLabel("", self)
        self.treeView = AutoSizingTreeView(self, minimumVisibleRows=3, maximumVisibleRows=16)
        self.treeModel = QStandardItemModel(self.treeView)

        self.selectAllButton = PrimaryPushButton(self.tr("全选"), self)
        self.clearButton = PushButton(self.tr("全不选"), self)
        self.invertButton = PushButton(self.tr("反选"), self)

        self._initWidget()
        self._initLayout()
        self._buildTree()
        self._updateSummary()

    def _initWidget(self) -> None:
        self.widget.setMinimumWidth(720)
        self.yesButton.setText(self.tr("应用"))
        self.cancelButton.setText(self.tr("取消"))

        self.treeModel.setHorizontalHeaderLabels([self.tr("文件"), self.tr("大小")])
        self.treeView.setModel(self.treeModel)
        self.treeView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.treeView.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.treeView.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.treeModel.itemChanged.connect(self._onItemChanged)

        self.selectAllButton.clicked.connect(lambda: self._setAll(True))
        self.clearButton.clicked.connect(lambda: self._setAll(False))
        self.invertButton.clicked.connect(self._invertSelection)

    def _initLayout(self) -> None:
        actionsLayout = QHBoxLayout()
        actionsLayout.setContentsMargins(0, 0, 0, 0)
        actionsLayout.setSpacing(8)
        actionsLayout.addWidget(self.selectAllButton)
        actionsLayout.addWidget(self.clearButton)
        actionsLayout.addWidget(self.invertButton)
        actionsLayout.addStretch(1)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.summaryLabel)
        self.viewLayout.addSpacing(8)
        self.viewLayout.addWidget(self.treeView)
        self.viewLayout.addSpacing(8)
        self.viewLayout.addLayout(actionsLayout)

    def _buildTree(self) -> None:
        folderItems: dict[tuple[str, ...], QStandardItem] = {}
        provider = QFileIconProvider()
        root = self.treeModel.invisibleRootItem()

        for file in self._task.files or []:
            path = PurePosixPath(file.relativePath)
            parts = path.parts
            parent = root
            prefix: list[str] = []

            for part in parts[:-1]:
                prefix.append(part)
                key = tuple(prefix)
                item = folderItems.get(key)
                if item is None:
                    item = QStandardItem(part)
                    item.setEditable(False)
                    item.setCheckable(True)
                    item.setIcon(provider.icon(QFileIconProvider.IconType.Folder))
                    parent.appendRow([item, QStandardItem("")])
                    folderItems[key] = item
                parent = item

            name = parts[-1] if parts else file.relativePath
            item = QStandardItem(name)
            item.setEditable(False)
            item.setCheckable(True)
            item.setCheckState(Qt.CheckState.Checked if file.selected else Qt.CheckState.Unchecked)
            parent.appendRow([item, QStandardItem(toReadableSize(file.size))])
            self._fileItems[file.index] = item

        with QSignalBlocker(self.treeModel):
            for i in range(root.rowCount()):
                self._updateBranchCheckState(root.child(i))

        self.treeView.expandAll()
        self.treeView.resizeColumnToContents(0)

    def selectedIndexes(self) -> set[int]:
        return {
            idx for idx, item in self._fileItems.items()
            if item.checkState() == Qt.CheckState.Checked
        }

    def validate(self) -> bool:
        return bool(self.selectedIndexes())

    def _onItemChanged(self, item: QStandardItem) -> None:
        state = item.checkState()
        with QSignalBlocker(self.treeModel):
            if item.rowCount() > 0:
                for i in range(item.rowCount()):
                    item.child(i).setCheckState(state)
            self._updateAncestorCheckStates(item.parent())
        self._updateSummary()

    def _updateBranchCheckState(self, item: QStandardItem) -> Qt.CheckState:
        if item.rowCount() == 0:
            return item.checkState()
        states = [self._updateBranchCheckState(item.child(i)) for i in range(item.rowCount())]
        if all(s == Qt.CheckState.Checked for s in states):
            item.setCheckState(Qt.CheckState.Checked)
        elif all(s == Qt.CheckState.Unchecked for s in states):
            item.setCheckState(Qt.CheckState.Unchecked)
        else:
            item.setCheckState(Qt.CheckState.PartiallyChecked)
        return item.checkState()

    def _updateAncestorCheckStates(self, item: QStandardItem | None) -> None:
        while item is not None:
            states = [item.child(i).checkState() for i in range(item.rowCount())]
            if all(s == Qt.CheckState.Checked for s in states):
                item.setCheckState(Qt.CheckState.Checked)
            elif all(s == Qt.CheckState.Unchecked for s in states):
                item.setCheckState(Qt.CheckState.Unchecked)
            else:
                item.setCheckState(Qt.CheckState.PartiallyChecked)
            item = item.parent()

    def _updateSummary(self) -> None:
        selected = self.selectedIndexes()
        total = len(self._fileItems)
        size = sum(
            f.size for f in (self._task.files or [])
            if f.index in selected
        )
        self.summaryLabel.setText(
            self.tr("已选择 {0}/{1} 个文件，共 {2}").format(len(selected), total, toReadableSize(size))
        )

    def _setAll(self, checked: bool) -> None:
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        with QSignalBlocker(self.treeModel):
            for item in self._fileItems.values():
                item.setCheckState(state)
            root = self.treeModel.invisibleRootItem()
            for i in range(root.rowCount()):
                self._updateBranchCheckState(root.child(i))
        self._updateSummary()

    def _invertSelection(self) -> None:
        with QSignalBlocker(self.treeModel):
            for item in self._fileItems.values():
                item.setCheckState(
                    Qt.CheckState.Unchecked if item.checkState() == Qt.CheckState.Checked else Qt.CheckState.Checked
                )
            root = self.treeModel.invisibleRootItem()
            for i in range(root.rowCount()):
                self._updateBranchCheckState(root.child(i))
        self._updateSummary()


from PySide6.QtWidgets import QFileIconProvider
from qfluentwidgets import FluentIcon, PrimaryPushButton, ToolButton

from app.format import toReadableSize, toReadableTime
from app.models.task import TaskStatus
from app.view.cards.draft_cards import UniversalDraftCard
from app.view.cards.task_cards import UniversalTaskCard
from app.view.dialogs.file_select import FileSelectDialog
from .task import BTTask


def openFileSelection(task: BTTask, parent) -> set[int] | None:
    dialog = TorrentFileSelectDialog(task, parent)
    try:
        if not dialog.exec():
            return None
        selectedIndexes = dialog.selectedIndexes()
        task.setSelection(selectedIndexes)
        return selectedIndexes
    finally:
        dialog.deleteLater()


class TorrentFileSelectDialog(FileSelectDialog):
    def _fileDisplayPath(self, file) -> str:
        task: BTTask = self.task
        return task.toRelativePath(file)

    def _fileTypePath(self, file) -> str:
        return file.relativePath


class BTDraftCard(UniversalDraftCard):
    def __init__(self, task: BTTask, parent=None):
        super().__init__(task, parent)

    @property
    def task(self) -> BTTask:
        return self._task

    def _initWidget(self):
        super()._initWidget()
        icon = QFileIconProvider.IconType.File if self.task.isSingleFile else QFileIconProvider.IconType.Folder
        self.iconLabel.setPixmap(QFileIconProvider().icon(icon).pixmap(20, 20))

    def _initLayout(self):
        super()._initLayout()
        if len(self.task.files) > 1:
            self._selectFilesButton = PrimaryPushButton(self.tr("选择文件"), self)
            self._selectFilesButton.clicked.connect(self._onSelectFilesClicked)
            self.hBoxLayout.addWidget(self._selectFilesButton)

    def _bind(self):
        super()._bind()

    def _refreshSummary(self):
        self.summaryLabel.setText(
            self.tr("{0}/{1} 个文件 · {2}").format(
                self.task.countSelected,
                len(self.task.files),
                toReadableSize(self.task.fileSize),
            )
        )

    def _onSelectFilesClicked(self):
        if openFileSelection(self.task, self.window()) is not None:
            self._refreshSummary()


class BTTaskCard(UniversalTaskCard):
    def __init__(self, task: BTTask, parent=None):
        super().__init__(task, parent)
        self.task: BTTask = task
        self.selectFilesButton = ToolButton(FluentIcon.LIBRARY, self)
        self.hBoxLayout.insertWidget(
            self.hBoxLayout.indexOf(self.verifyHashButton),
            self.selectFilesButton,
        )
        self.selectFilesButton.clicked.connect(self._onSelectFilesClicked)

    def _refreshTransferInfo(self):
        if self.task.status == TaskStatus.RUNNING:
            self.speedLabel.setText(f"{toReadableSize(self.task.downloadRate)}/s")
            if self.task.fileSize > 0 and self.task.downloadRate > 0 and not self.task.isSeeding:
                remaining = self.task.fileSize - self.task.step.receivedBytes
                self.leftTimeLabel.setText(toReadableTime(int(remaining / self.task.downloadRate)))
            self.speedLabel.show()

    def _onSelectFilesClicked(self):
        previousSelected = {f.index for f in self.task.files if f.selected}
        selectedIndexes = openFileSelection(self.task, self.window())
        if selectedIndexes is None:
            return
        self._refreshTransferInfo()

    def refresh(self):
        super().refresh()
        self._refreshTransferInfo()
        self.selectFilesButton.setEnabled(
            self.task.status != TaskStatus.COMPLETED or any(not f.selected for f in self.task.files)
        )


from PySide6.QtWidgets import QFileIconProvider, QWidget
from qfluentwidgets import FluentIcon, ToolButton

from app.format import toReadableSize
from app.models.task import TaskStatus
from app.view.cards.draft_cards import UniversalDraftCard
from app.view.cards.task_cards import UniversalTaskCard
from app.view.dialogs.file_select import FileSelectDialog
from .task import FtpTask


def openFileSelection(task: FtpTask, parent) -> set[int] | None:
    dialog = FileSelectDialog(task, parent)
    try:
        if not dialog.exec():
            return None
        selectedIndexes = dialog.selectedIndexes()
        task.setSelection(selectedIndexes)
        return selectedIndexes
    finally:
        dialog.deleteLater()


class FtpFileSelectDialog(FileSelectDialog):
    def _fileDisplayPath(self, file) -> str:
        return file.relativePath


class FtpDraftCard(UniversalDraftCard):

    @property
    def task(self) -> FtpTask:
        return self._task

    def _initWidget(self):
        super()._initWidget()
        self._selectFilesButton = None
        if self.task.files and len(self.task.files) > 1:
            from qfluentwidgets import PrimaryPushButton
            self._selectFilesButton = PrimaryPushButton(self.tr("选择文件"), self)

    def _initLayout(self):
        super()._initLayout()
        if self._selectFilesButton is not None:
            self.layout().addWidget(self._selectFilesButton)

    def _bind(self):
        super()._bind()
        if self._selectFilesButton is not None:
            self._selectFilesButton.clicked.connect(self._onSelectFilesClicked)

    def _refreshSummary(self):
        if not self.task.files or len(self.task.files) <= 1:
            self.summaryLabel.setText(toReadableSize(self.task.fileSize))
            return
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

    def _onNameEdited(self):
        newName = self.nameEdit.text().strip()
        if newName and newName != self.task.name:
            self.task.setName(newName)
        self.nameLabel.setText(self.task.name)
        self.nameEdit.setText(self.task.name)
        self.nameEdit.hide()
        self.nameLabel.show()


class FtpTaskCard(UniversalTaskCard):
    def __init__(self, task: FtpTask, parent=None):
        super().__init__(task, parent)
        self.task: FtpTask = task
        self.selectFilesButton = ToolButton(FluentIcon.LIBRARY, self)
        self.hBoxLayout.insertWidget(
            self.hBoxLayout.indexOf(self.verifyHashButton),
            self.selectFilesButton,
        )
        self.selectFilesButton.clicked.connect(self._onSelectFilesClicked)

    def refresh(self):
        super().refresh()
        hasMultipleFiles = self.task.files and len(self.task.files) > 1
        self.selectFilesButton.setVisible(hasMultipleFiles)
        self.selectFilesButton.setEnabled(self.task.status != TaskStatus.RUNNING)

        if self.task.status in {TaskStatus.WAITING, TaskStatus.COMPLETED} and hasMultipleFiles:
            selected = sum(1 for f in self.task.files if f.selected)
            self.statusLabel.setText(self.tr("{0}/{1} 个文件").format(selected, len(self.task.files)))

    def _onSelectFilesClicked(self):
        if self.task.status == TaskStatus.RUNNING:
            return
        openFileSelection(self.task, self.window())

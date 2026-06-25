from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QTextOption
from PySide6.QtWidgets import QDialog, QFileDialog, QHBoxLayout
from qfluentwidgets import (
    FluentIcon,
    IndeterminateProgressBar,
    InfoBar,
    InfoBarPosition,
    MessageBoxBase,
    PushButton,
    SubtitleLabel,
)

from app.services.feature_service import featureService
from app.view.components.card_groups import DraftCardGroup, OptionCardGroup
from app.view.components.editors import AutoSizingEdit
from app.view.components.option_cards import SelectFolderCard, SubworkerCountCard

if TYPE_CHECKING:
    from app.models.task import Task
    from app.services.task_draft import TaskDraft
    from app.view.cards.draft_cards import DraftCard


class TaskDraftDialog(MessageBoxBase):

    def __init__(self, draft: TaskDraft, parent=None):
        super().__init__(parent)
        self._draft = draft
        self._parseTimer = QTimer(self, singleShot=True)
        self._cardByUrl: dict[str, DraftCard] = {}

        self.titleLabel = SubtitleLabel(self.tr("添加任务"), self)
        self.urlEdit = AutoSizingEdit(self)
        self.progressBar = IndeterminateProgressBar(self)
        self.resultGroup = DraftCardGroup(self)
        self.optionGroup = OptionCardGroup(self)
        self.importButton = PushButton(FluentIcon.FOLDER_ADD, self.tr("导入文件"), self)
        self.headerLayout = QHBoxLayout()

        self._initWidget()
        self._initLayout()
        self._bind()

    def _initWidget(self) -> None:
        self.widget.setFixedWidth(700)
        self.urlEdit.setPlaceholderText(self.tr("添加多个下载链接时，请确保每行只有一个下载链接"))
        self.urlEdit.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.progressBar.hide()
        self._fileTypes = featureService.fileTypes()
        self.importButton.setVisible(bool(self._fileTypes))

        self.optionGroup.addCard(SelectFolderCard(self.optionGroup))
        self.optionGroup.addCard(SubworkerCountCard(self.optionGroup))

    def _initLayout(self) -> None:
        self.headerLayout.addWidget(self.titleLabel)
        self.headerLayout.addStretch(1)
        self.headerLayout.addWidget(self.importButton)
        self.viewLayout.addLayout(self.headerLayout)
        self.viewLayout.addWidget(self.urlEdit)
        self.viewLayout.addWidget(self.progressBar)
        self.viewLayout.addWidget(self.resultGroup)
        self.viewLayout.addWidget(self.optionGroup)

    def _bind(self) -> None:
        self._parseTimer.setInterval(1000)
        self._parseTimer.timeout.connect(self._onParseNeeded)
        self.urlEdit.textChanged.connect(self._parseTimer.start)

        self._draft.parsingBusyChanged.connect(self.progressBar.setVisible)
        self._draft.parseSucceeded.connect(self._onParseSucceeded)
        self._draft.parseFailed.connect(self._onParseFailed)
        self._draft.itemsChanged.connect(self._onItemsChanged)
        self._draft.itemsCleared.connect(self._onCleared)

        self.importButton.clicked.connect(self._onImportClicked)

    def showStandalone(self) -> None:
        if self.isVisible():
            from app.platform.desktop import raiseWindow
            raiseWindow(self)
            return
        self.windowMask.hide()
        self.resize(740, 600)
        self.show()
        self.raise_()
        self.activateWindow()

    def showMask(self) -> int:
        self.windowMask.show()
        parent = self.parentWidget()
        if parent is not None:
            self.setGeometry(0, 0, parent.width(), parent.height())
            self.windowMask.resize(self.size())
        self.setShadowEffect(60, (0, 10), QColor(0, 0, 0, 50))
        self.setMaskColor(QColor(0, 0, 0, 76))
        return self.exec()

    def addUrls(self, urls: list[str]) -> None:
        if not urls:
            return
        existing = set(self._urls())
        toAdd = [stripped for u in urls if (stripped := u.strip()) and stripped not in existing]
        if not toAdd:
            return
        self.urlEdit.appendPlainText("\n".join(toAdd))
        self._parseTimer.stop()
        self._onParseNeeded()

    def addParsedTasks(self, tasks: list[Task]) -> None:
        if not tasks:
            return
        newUrls = self._draft.addParsedTasks(tasks)
        if newUrls:
            self.urlEdit.appendPlainText("\n".join(newUrls))
        self._parseTimer.stop()

    def done(self, code: int) -> None:
        if code == QDialog.DialogCode.Accepted:
            self._draft.confirm()
        else:
            self._draft.clear()

        self.urlEdit.clear()
        self.optionGroup.reset()
        self._parseTimer.stop()
        super().done(code)

    def validate(self) -> bool:
        self._parseTimer.stop()
        self._onParseNeeded()
        return self._draft.canConfirm()

    def _onParseNeeded(self) -> None:
        self._draft.setBaseOptions(self.optionGroup.options())
        self._draft.setUrls(self._urls())

    def _onParseSucceeded(self, url: str, task: Task) -> None:
        card = featureService.draftCard(task, self.resultGroup)
        card.categoryPicked.connect(lambda cid: self._draft.setUrlCategory(url, cid))
        card.editRequested.connect(lambda u=url: self._onEditRequested(u))
        self.resultGroup.addCard(card)
        self._cardByUrl[url] = card

    def _onEditRequested(self, url: str) -> None:
        from app.view.dialogs.edit_task import DraftEditDialog

        task = self._draft.taskByUrl(url)
        if task is None:
            return
        dialog = DraftEditDialog(task, parent=self.window())
        dialog.exec()

    def _onParseFailed(self, url: str, error: str) -> None:
        displayUrl = url if len(url) <= 48 else f"{url[:45]}..."
        InfoBar.error(
            self.tr("链接解析失败"),
            f"{displayUrl}\n{error}",
            duration=-1,
            position=InfoBarPosition.BOTTOM_RIGHT,
            parent=self,
        )

    def _onItemsChanged(self) -> None:
        currentUrls = set(self._draft.urls())
        for url in list(self._cardByUrl):
            if url not in currentUrls:
                card = self._cardByUrl.pop(url)
                self.resultGroup.scrollLayout.removeWidget(card)
                card.deleteLater()
        for i, url in enumerate(self._draft.urls()):
            card = self._cardByUrl.get(url)
            if card is not None:
                layout = self.resultGroup.scrollLayout
                if layout.indexOf(card) != i:
                    layout.insertWidget(i, card, alignment=Qt.AlignmentFlag.AlignTop)

    def _onCleared(self) -> None:
        self._cardByUrl.clear()
        self.resultGroup.clear()

    def _urls(self) -> list[str]:
        text = self.urlEdit.toPlainText()
        if not text:
            return []
        return [line.strip() for line in text.splitlines() if line.strip()]

    def _onImportClicked(self) -> None:
        globs = [f"*{ext}" for ft in self._fileTypes for ext in ft.extensions]
        nameFilters = [self.tr("所有可导入文件 ({0})").format(" ".join(globs))]
        nameFilters += [
            f"{ft.displayName} ({' '.join(f'*{ext}' for ext in ft.extensions)})"
            for ft in self._fileTypes
        ]
        paths, _ = QFileDialog.getOpenFileNames(self, self.tr("导入文件"), "", ";;".join(nameFilters))
        if paths:
            self.addUrls([Path(p).as_uri() for p in paths])

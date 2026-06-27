from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import (
    CheckBox, ComboBox, FluentIcon, MessageBoxBase,
    ToolTipFilter, TransparentToolButton,
)

from app.format import toReadableSize
from app.view.cards.draft_cards import UniversalDraftCard
from .task import BilibiliTask, DownloadMode

MODE_LABELS = ("视频", "音频", "封面")


class BilibiliDraftCard(UniversalDraftCard):

    def _initWidget(self):
        super()._initWidget()
        self._modeCombo = ComboBox(self)
        self._modeCombo.setMinimumWidth(80)
        for label in MODE_LABELS:
            self._modeCombo.addItem(self.tr(label))
        self._modeCombo.setCurrentIndex(self.task.mode.value)

        self._selectPagesButton = TransparentToolButton(FluentIcon.DOCUMENT, self)
        self._selectPagesButton.installEventFilter(ToolTipFilter(self._selectPagesButton))
        self._selectPagesButton.setToolTip(self.tr("选择分P"))
        self._refreshPageButtonVisibility()

    def _initLayout(self):
        super()._initLayout()
        self.layout().addWidget(self._modeCombo)
        self.layout().addWidget(self._selectPagesButton)

    def _bind(self):
        super()._bind()
        self._modeCombo.currentIndexChanged.connect(self._onModeChanged)
        self._selectPagesButton.clicked.connect(self._onSelectPagesClicked)

    def _onModeChanged(self, index: int):
        task: BilibiliTask = self._task
        task.setMode(DownloadMode(index))
        self._refreshBilibiliInfo()

    def _onSelectPagesClicked(self):
        task: BilibiliTask = self._task
        dialog = PageSelectDialog(task, self.window())
        if dialog.exec():
            selected = dialog.selectedPageNumbers()
            if selected:
                task.setPageSelection(selected)
                self._refreshBilibiliInfo()

    def _refreshBilibiliInfo(self):
        self.sizeLabel.setText(toReadableSize(self._task.fileSize))
        self.nameLabel.setText(self._task.name)
        self._refreshPageButtonVisibility()

    def _refreshPageButtonVisibility(self):
        task: BilibiliTask = self._task
        visible = task.mode != DownloadMode.COVER and len(task.pages) > 1
        self._selectPagesButton.setVisible(visible)


class PageSelectDialog(MessageBoxBase):

    def __init__(self, task: BilibiliTask, parent=None):
        super().__init__(parent)
        self._checkboxes: list[tuple[int, CheckBox]] = []

        self.yesButton.setText(self.tr("确定"))
        self.cancelButton.setText(self.tr("取消"))

        scrollWidget = QWidget(self)
        scrollLayout = QVBoxLayout(scrollWidget)
        scrollLayout.setContentsMargins(0, 0, 0, 0)
        scrollLayout.setSpacing(8)

        for page in task.pages:
            pageNumber = page["pageNumber"]
            pagePart = page.get("pagePart", "").strip()
            label = f"P{pageNumber}"
            if pagePart:
                label += f": {pagePart}"

            cb = CheckBox(label, scrollWidget)
            cb.setChecked(page.get("selected", True))
            scrollLayout.addWidget(cb)
            self._checkboxes.append((pageNumber, cb))

        self.viewLayout.addWidget(scrollWidget)
        self.widget.setMinimumWidth(400)

    def selectedPageNumbers(self) -> set[int]:
        return {num for num, cb in self._checkboxes if cb.isChecked()}

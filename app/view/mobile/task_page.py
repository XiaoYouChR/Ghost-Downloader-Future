from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    Action, FluentIcon, PrimaryToolButton, RoundMenu, SearchLineEdit, ToolButton,
)

from app.view.pages.task_page import FilterMode, SortField, TaskPage


class MobileTaskPage(QWidget):
    selectionModeChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.taskPage = TaskPage(self)
        self.toolBar = QWidget(self)
        self.startAllButton = PrimaryToolButton(FluentIcon.PLAY, self)
        self.pauseAllButton = ToolButton(FluentIcon.PAUSE, self)
        self.filterButton = ToolButton(FluentIcon.FILTER, self)
        self.sortButton = ToolButton(FluentIcon.MENU, self)
        self.searchLineEdit = SearchLineEdit(self)

        self._initWidget()
        self._initLayout()
        self._bind()

    @property
    def isSelectionMode(self) -> bool:
        return self.taskPage.isSelectionMode

    def setSelectionMode(self, enter: bool) -> None:
        self.taskPage.setSelectionMode(enter)
        self.selectionModeChanged.emit(enter)

    def _initWidget(self) -> None:
        self.startAllButton.setToolTip(self.tr("全部开始"))
        self.pauseAllButton.setToolTip(self.tr("全部暂停"))
        self.filterButton.setToolTip(self.tr("筛选"))
        self.sortButton.setToolTip(self.tr("排序"))
        self.searchLineEdit.setPlaceholderText(self.tr("搜索任务"))

    def _initLayout(self) -> None:
        toolBarLayout = QHBoxLayout(self.toolBar)
        toolBarLayout.setContentsMargins(10, 6, 10, 6)
        toolBarLayout.setSpacing(6)
        toolBarLayout.addWidget(self.startAllButton)
        toolBarLayout.addWidget(self.pauseAllButton)
        toolBarLayout.addWidget(self.searchLineEdit, 1)
        toolBarLayout.addWidget(self.filterButton)
        toolBarLayout.addWidget(self.sortButton)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toolBar)
        layout.addWidget(self.taskPage, 1)

    def _bind(self) -> None:
        self.startAllButton.clicked.connect(self.taskPage.startAll)
        self.pauseAllButton.clicked.connect(self.taskPage.pauseAll)
        self.searchLineEdit.textChanged.connect(self.taskPage.setSearchText)
        self.filterButton.clicked.connect(self._showFilterMenu)
        self.sortButton.clicked.connect(self._showSortMenu)

    def _showFilterMenu(self) -> None:
        items = [
            (FilterMode.ALL, self.tr("全部")),
            (FilterMode.RUNNING, self.tr("下载中")),
            (FilterMode.WAITING, self.tr("等待中")),
            (FilterMode.PAUSED, self.tr("已暂停")),
            (FilterMode.COMPLETED, self.tr("已完成")),
            (FilterMode.FAILED, self.tr("失败")),
        ]
        menu = RoundMenu(parent=self)
        for mode, label in items:
            action = Action(label, self)
            action.triggered.connect(lambda _=False, m=mode: self.taskPage.setFilterMode(m))
            menu.addAction(action)
        menu.exec(self.filterButton.mapToGlobal(self.filterButton.rect().bottomLeft()))

    def _showSortMenu(self) -> None:
        items = [
            (SortField.CREATED_AT, self.tr("添加时间")),
            (SortField.NAME, self.tr("名称")),
            (SortField.SIZE, self.tr("大小")),
        ]
        menu = RoundMenu(parent=self)
        for field, label in items:
            action = Action(label, self)
            action.triggered.connect(lambda _=False, f=field: self.taskPage.setSortField(f))
            menu.addAction(action)
        menu.addSeparator()
        ascending = self.taskPage.isSortAscending
        orderAction = Action(
            FluentIcon.UP if ascending else FluentIcon.DOWN,
            self.tr("升序") if ascending else self.tr("降序"),
            self,
        )
        orderAction.triggered.connect(self._toggleSortOrder)
        menu.addAction(orderAction)
        menu.exec(self.sortButton.mapToGlobal(self.sortButton.rect().bottomLeft()))

    def _toggleSortOrder(self) -> None:
        self.taskPage.setSortOrder(not self.taskPage.isSortAscending)

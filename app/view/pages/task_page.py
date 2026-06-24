from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import ScrollArea

from app.models.task import TaskStatus
from app.services.feature_service import featureService
from app.services.task_service import taskService

if TYPE_CHECKING:
    from app.models.task import Task
    from app.view.cards.task_cards import TaskCard


class FilterMode(IntEnum):
    ALL = 0
    RUNNING = 1
    WAITING = 2
    PAUSED = 3
    COMPLETED = 4
    FAILED = 5


FILTER_TO_STATUS = {
    FilterMode.RUNNING: TaskStatus.RUNNING,
    FilterMode.WAITING: TaskStatus.WAITING,
    FilterMode.PAUSED: TaskStatus.PAUSED,
    FilterMode.COMPLETED: TaskStatus.COMPLETED,
    FilterMode.FAILED: TaskStatus.FAILED,
}


class SortField(IntEnum):
    CREATED_AT = 0
    NAME = 1
    SIZE = 2


class TaskPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filterMode = FilterMode.ALL
        self._categoryFilter = ""
        self._sortField = SortField.CREATED_AT
        self._sortAscending = False
        self._searchText = ""
        self._selectionMode = False
        self._cards: dict[str, TaskCard] = {}
        self._displayOrder: list[str] = []

        self._refreshTimer = QTimer(self, singleShot=True)
        self._refreshTimer.setInterval(1000)
        self._refreshTimer.timeout.connect(self._refreshVisibleCards)

        self.scrollArea = ScrollArea(self)
        self.scrollWidget = QWidget(self)
        self.scrollLayout = QVBoxLayout(self.scrollWidget)

        self._initWidget()
        self._initLayout()
        self._bind()

    def _initWidget(self) -> None:
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.enableTransparentBackground()
        self.scrollLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollLayout.setSpacing(2)
        self.scrollLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def _initLayout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scrollArea)

    def _bind(self) -> None:
        taskService.taskAdded.connect(self._onTaskAdded)
        taskService.taskRemoved.connect(self._onTaskRemoved)
        self._refreshTimer.start()

    def setFilterMode(self, mode: FilterMode) -> None:
        self._filterMode = mode
        self._rebuildList()

    def setCategoryFilter(self, categoryId: str) -> None:
        self._categoryFilter = categoryId
        self._rebuildList()

    def setSortField(self, field: SortField) -> None:
        self._sortField = field
        self._rebuildList()

    def setSortOrder(self, ascending: bool) -> None:
        self._sortAscending = ascending
        self._rebuildList()

    def startAll(self) -> None:
        taskService.startAll()

    def pauseAll(self) -> None:
        taskService.pauseAll()

    def selectAll(self) -> None:
        for taskId in self._displayOrder:
            card = self._cards.get(taskId)
            if card:
                card.setChecked(True)

    def invertSelection(self) -> None:
        for taskId in self._displayOrder:
            card = self._cards.get(taskId)
            if card:
                card.setChecked(not card.isChecked())

    def setSelectionMode(self, enter: bool) -> None:
        self._selectionMode = enter
        for card in self._cards.values():
            card.setSelectionMode(enter)

    def _rebuildList(self) -> None:
        tasks = list(taskService.tasks.values())

        if self._filterMode != FilterMode.ALL:
            status = FILTER_TO_STATUS.get(self._filterMode)
            if status is not None:
                tasks = [t for t in tasks if t.status == status]

        if self._categoryFilter:
            tasks = [t for t in tasks if t.category == self._categoryFilter]

        if self._searchText:
            lower = self._searchText.lower()
            tasks = [t for t in tasks if lower in t.name.lower() or lower in t.url.lower()]

        if self._sortField == SortField.NAME:
            tasks.sort(key=lambda t: t.name.lower(), reverse=not self._sortAscending)
        elif self._sortField == SortField.SIZE:
            tasks.sort(key=lambda t: t.fileSize, reverse=not self._sortAscending)
        else:
            tasks.sort(key=lambda t: t.createdAt, reverse=not self._sortAscending)

        self._displayOrder = [t.taskId for t in tasks]
        self._refreshViewport()

    def _refreshViewport(self) -> None:
        while self.scrollLayout.count():
            self.scrollLayout.takeAt(0)

        for taskId in self._displayOrder:
            card = self._cards.get(taskId)
            if card:
                self.scrollLayout.addWidget(card, alignment=Qt.AlignmentFlag.AlignTop)

    def _refreshVisibleCards(self) -> None:
        for card in self._cards.values():
            card.refresh()
        self._refreshTimer.start()

    def _onDeleteConfirmed(self, shouldDeleteFiles: bool) -> None:
        toDelete = [
            taskId for taskId in self._displayOrder
            if (card := self._cards.get(taskId)) and card.isChecked()
        ]
        for taskId in toDelete:
            task = taskService.taskById(taskId)
            if task:
                taskService.delete(task, shouldDeleteFiles)

    def _onTaskAdded(self, task: Task) -> None:
        card = featureService.taskCard(task, self.scrollWidget)
        self._cards[task.taskId] = card
        card.setSelectionMode(self._selectionMode)
        self._rebuildList()

    def _onTaskRemoved(self, taskId: str) -> None:
        card = self._cards.pop(taskId, None)
        if card:
            self.scrollLayout.removeWidget(card)
            card.deleteLater()
        if taskId in self._displayOrder:
            self._displayOrder.remove(taskId)

    def _onSearchTextChanged(self, text: str) -> None:
        self._searchText = text
        self._rebuildList()

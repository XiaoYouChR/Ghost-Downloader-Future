from enum import IntEnum

from PySide6.QtWidgets import QWidget


class FilterMode(IntEnum):
    ALL = 0
    RUNNING = 1
    WAITING = 2
    PAUSED = 3
    COMPLETED = 4
    FAILED = 5


class SortField(IntEnum):
    CREATED_AT = 0
    NAME = 1
    SIZE = 2


class TaskPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def setFilterMode(self, mode: FilterMode) -> None:
        pass

    def setCategoryFilter(self, categoryId: str) -> None:
        pass

    def setSortField(self, field: SortField) -> None:
        pass

    def setSortOrder(self, ascending: bool) -> None:
        pass

    def startAll(self) -> None:
        pass

    def pauseAll(self) -> None:
        pass

    def selectAll(self) -> None:
        pass

    def invertSelection(self) -> None:
        pass

    def setSelectionMode(self, enter: bool) -> None:
        pass

    def _rebuildList(self) -> None:
        pass

    def _refreshViewport(self) -> None:
        pass

    def _refreshVisibleCards(self) -> None:
        pass

    def _onDeleteConfirmed(self, shouldDeleteFiles: bool) -> None:
        pass

    def _onTaskAdded(self, task) -> None:
        pass

    def _onTaskRemoved(self, taskId: str) -> None:
        pass

    def _onSearchTextChanged(self, text: str) -> None:
        pass

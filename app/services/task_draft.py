from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, TYPE_CHECKING

from PySide6.QtCore import QObject, Signal
from loguru import logger

if TYPE_CHECKING:
    from app.models.task import Task


@dataclass
class DraftItem:
    url: str
    parseId: str = ""
    task: Task | None = None


class TaskDraft(QObject):
    parsingBusyChanged = Signal(bool)
    parseSucceeded = Signal(str, object)
    parseFailed = Signal(str, str)
    itemsReordered = Signal()
    cleared = Signal()
    taskConfirmed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[DraftItem] = []
        self._parsing: dict[str, DraftItem] = {}
        self._accepted: dict[str, dict[str, Any]] = {}
        self._overrides: dict[str, dict[str, Any]] = {}
        self._baseOptions: dict[str, Any] = {}

    def urls(self) -> list[str]:
        return [item.url for item in self._items]

    def taskByUrl(self, url: str) -> Task | None:
        for item in self._items:
            if item.url == url:
                return item.task
        return None

    def canAccept(self) -> bool:
        return any(item.parseId or item.task is not None for item in self._items)

    def setBaseOptions(self, options: dict) -> None:
        self._baseOptions = options
        for item in self._items:
            if item.task is not None:
                item.task.setOptions(self._buildOptions(item.url))

    def setUrlCategory(self, url: str, categoryId: str) -> None:
        self._overrides[url] = {"category": categoryId}

    def setUrls(self, urls: list[str]) -> None:
        from app.models.task import TaskOptions
        from app.models.serialization import filterFields
        from app.services.coroutine_runner import coroutineRunner
        from app.services.feature_service import featureService

        previous = self._items
        previousUrls = [item.url for item in previous]
        nextItems: list[DraftItem] = []
        matcher = SequenceMatcher(a=previousUrls, b=urls, autojunk=False)

        for tag, oldStart, oldEnd, newStart, newEnd in matcher.get_opcodes():
            if tag == "equal":
                nextItems.extend(previous[oldStart:oldEnd])
                continue
            for item in previous[oldStart:oldEnd]:
                if item.parseId:
                    self._parsing.pop(item.parseId, None)
                    coroutineRunner.cancel(item.parseId)
            if not self._parsing:
                self.parsingBusyChanged.emit(False)
            for url in urls[newStart:newEnd]:
                item = DraftItem(url=url)
                try:
                    options = TaskOptions(**filterFields(TaskOptions, {**self._baseOptions, "url": url}))
                    parseId = coroutineRunner.submit(
                        featureService.parse(options),
                        done=lambda result: self._onParseFinished(parseId, result, None),
                        failed=lambda error: self._onParseFinished(parseId, None, error),
                    )
                except Exception as e:
                    logger.opt(exception=e).error("提交解析请求失败 {}", url)
                    self.parseFailed.emit(url, repr(e))
                    nextItems.append(item)
                    continue
                item.parseId = parseId
                self._parsing[parseId] = item
                self.parsingBusyChanged.emit(True)
                nextItems.append(item)

        self._items = nextItems
        activeUrls = set(urls)
        self._overrides = {u: o for u, o in self._overrides.items() if u in activeUrls}
        self.itemsReordered.emit()

    def addParsedTasks(self, tasks: list[Task]) -> list[str]:
        from app.services.coroutine_runner import coroutineRunner

        if not tasks:
            return []

        byUrl = {item.url: item for item in self._items}
        newUrls: list[str] = []

        for task in tasks:
            url = task.url
            item = byUrl.get(url)
            if item is not None:
                if item.task is not None:
                    continue
                if item.parseId:
                    self._parsing.pop(item.parseId, None)
                    coroutineRunner.cancel(item.parseId)
                    self.parsingBusyChanged.emit(bool(self._parsing))
            else:
                newUrls.append(url)
                item = DraftItem(url=url)
                self._items.append(item)
                byUrl[url] = item

            task.setOptions(self._buildOptions(url))
            item.task = task
            self.parseSucceeded.emit(url, task)

        self.itemsReordered.emit()
        return newUrls

    def accept(self) -> list[Task]:
        from app.services.coroutine_runner import coroutineRunner

        confirmed: list[Task] = []

        for item in self._items:
            if item.task is not None:
                item.task.setOptions(self._buildOptions(item.url))
                confirmed.append(item.task)
                continue
            if not item.parseId:
                continue
            self._parsing.pop(item.parseId, None)
            self._accepted[item.parseId] = self._buildOptions(item.url)

        self.parsingBusyChanged.emit(bool(self._parsing))

        for item in self._items:
            if item.parseId and item.parseId not in self._accepted:
                coroutineRunner.cancel(item.parseId)

        self._items.clear()
        self._overrides.clear()
        self.cleared.emit()
        return confirmed

    def clear(self) -> None:
        from app.services.coroutine_runner import coroutineRunner
        for item in self._items:
            if item.parseId:
                self._parsing.pop(item.parseId, None)
                coroutineRunner.cancel(item.parseId)
        self._items.clear()
        self._overrides.clear()
        self.cleared.emit()
        self.parsingBusyChanged.emit(bool(self._parsing))

    def _buildOptions(self, url: str) -> dict[str, Any]:
        options = self._baseOptions.copy()
        options.update(self._overrides.get(url, {}))
        return options

    def _onParseFinished(self, parseId: str, resultTask: Task | None, error: str | None) -> None:
        item = self._parsing.pop(parseId, None)
        if item is not None:
            self.parsingBusyChanged.emit(bool(self._parsing))
            item.parseId = ""

            if error or resultTask is None:
                item.task = None
                self.parseFailed.emit(item.url, error or "解析失败")
                if error:
                    logger.warning("解析任务失败 {}: {}", item.url, error)
                return

            resultTask.setOptions(self._buildOptions(item.url))
            item.task = resultTask
            self.parseSucceeded.emit(item.url, resultTask)
            self.itemsReordered.emit()
            return

        acceptedOptions = self._accepted.pop(parseId, None)
        if acceptedOptions is None:
            return

        if error or resultTask is None:
            if error:
                logger.warning("后台确认任务解析失败: {}", error)
            return

        resultTask.setOptions(acceptedOptions)
        self.taskConfirmed.emit(resultTask)

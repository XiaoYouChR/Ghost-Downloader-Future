from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QPaintEvent
from PySide6.QtWidgets import QWidget

from app.view.cards.task_cards import UniversalTaskCard
from .task import HttpTaskStep


class SegmentedProgressBar(QWidget):
    def __init__(self, step: HttpTaskStep, parent=None):
        super().__init__(parent)
        self._step = step

    def setValue(self, value: float): ...
    def setError(self, error: bool): ...
    def error(self) -> bool: ...
    def pause(self): ...
    def barColor(self) -> QColor: ...
    def paintEvent(self, event: QPaintEvent): ...


class HttpTaskCard(UniversalTaskCard):
    def createProgressBar(self) -> QWidget:
        step = self.task.steps[0] if self.task.steps else None
        if isinstance(step, HttpTaskStep) and step.supportsRange and step.subworkerCount > 1:
            return SegmentedProgressBar(step, self)
        return super().createProgressBar()

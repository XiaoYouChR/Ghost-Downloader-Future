from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from app.view.cards.draft_cards import UniversalDraftCard
from app.view.cards.task_cards import UniversalTaskCard


class M3U8DraftCard(UniversalDraftCard):
    def __init__(self, task, parent=None):
        super().__init__(task, parent)

    @property
    def task(self):
        return self._task

    def _initWidget(self): ...
    def _initLayout(self): ...

    def _onNameEdited(self): ...


class M3U8TaskCard(UniversalTaskCard):
    def refresh(self): ...


class M3U8LiveTaskCard(M3U8TaskCard):
    def refresh(self): ...
    def _refreshToggleButton(self): ...


class M3U8OptionCard(QWidget):
    optionsChanged = Signal()

    @property
    def options(self) -> dict: ...


class StreamSelectCard(M3U8OptionCard):
    def __init__(self, icon, title: str, parent=None, *, streams: list, initial: str = ""):
        super().__init__(parent)

    def _initWidget(self): ...
    def _initLayout(self): ...
    def _bind(self): ...


class RecordLimitCard(M3U8OptionCard):
    def __init__(self, icon, title: str, parent=None, *, initial: str = ""):
        super().__init__(parent)

    def _initWidget(self): ...
    def _initLayout(self): ...
    def _bind(self): ...


class DecryptionKeyCard(M3U8OptionCard):
    def __init__(self, icon, title: str, parent=None, *, keys: list | None = None, keyTextFile: str = ""):
        super().__init__(parent)

    def _initWidget(self): ...
    def _initLayout(self): ...
    def _bind(self): ...


class MuxImportCard(M3U8OptionCard):
    def __init__(self, icon, title: str, parent=None, *, initial: list | None = None):
        super().__init__(parent)

    def _initWidget(self): ...
    def _initLayout(self): ...
    def _bind(self): ...

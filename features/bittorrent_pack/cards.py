from app.view.cards.draft_cards import UniversalDraftCard
from app.view.cards.task_cards import UniversalTaskCard
from app.view.components.file_select_dialog import FileSelectDialog
from .task import BTTask


class TorrentFileSelectDialog(FileSelectDialog):
    def _fileDisplayPath(self, file) -> str: ...
    def _fileTypePath(self, file) -> str: ...


class BTDraftCard(UniversalDraftCard):
    def __init__(self, task: BTTask, parent=None):
        super().__init__(task, parent)

    @property
    def task(self) -> BTTask:
        return self._task

    def _initWidget(self): ...
    def _initLayout(self): ...
    def _bind(self): ...

    def _refreshSummary(self): ...
    def _onSelectFilesClicked(self): ...


class BTTaskCard(UniversalTaskCard):
    def __init__(self, task: BTTask, parent=None):
        super().__init__(task, parent)

    def refresh(self): ...
    def _refreshTransferInfo(self): ...
    def _onSelectFilesClicked(self): ...

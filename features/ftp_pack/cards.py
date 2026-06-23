from app.view.cards.draft_cards import UniversalDraftCard
from app.view.cards.task_cards import UniversalTaskCard
from app.view.components.file_select_dialog import FileSelectDialog
from .task import FtpTask


class FtpFileSelectDialog(FileSelectDialog):
    def _fileDisplayPath(self, file) -> str: ...


class FtpDraftCard(UniversalDraftCard):
    def __init__(self, task: FtpTask, parent=None):
        super().__init__(task, parent)

    @property
    def task(self) -> FtpTask:
        return self._task

    def _initWidget(self): ...
    def _initLayout(self): ...

    def _refreshSummary(self): ...
    def _onSelectFilesClicked(self): ...
    def _onNameEdited(self): ...


class FtpTaskCard(UniversalTaskCard):
    def __init__(self, task: FtpTask, parent=None):
        super().__init__(task, parent)

    def statusInfoText(self) -> str | None: ...
    def refresh(self): ...
    def _onSelectFilesClicked(self): ...

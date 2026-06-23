from PySide6.QtCore import Signal

from app.view.cards.draft_cards import UniversalDraftCard

QUALITY_TIERS = (
    ("best", "Best"),
    ("2160", "4K"),
    ("1440", "1440p"),
    ("1080", "1080p"),
    ("720", "720p"),
    ("480", "480p"),
)


class YtDlpDraftCard(UniversalDraftCard):
    optionsChanged = Signal()

    def __init__(self, task, parent=None):
        super().__init__(task, parent)

    def _initWidget(self): ...
    def _initLayout(self): ...
    def _bind(self): ...

    def _onQualityChanged(self, index: int):
        self.optionsChanged.emit()

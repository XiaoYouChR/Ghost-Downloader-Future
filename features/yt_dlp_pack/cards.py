from PySide6.QtCore import Signal
from qfluentwidgets import ComboBox

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

    def _initWidget(self):
        super()._initWidget()
        self.qualityCombo = ComboBox(self)
        self.qualityCombo.setMinimumWidth(120)
        for value, label in QUALITY_TIERS:
            self.qualityCombo.addItem(label, userData=value)
        self.qualityCombo.setCurrentIndex(0)

    def _initLayout(self):
        super()._initLayout()
        self.layout().insertWidget(self.layout().count() - 1, self.qualityCombo)

    def _bind(self):
        super()._bind()
        self.qualityCombo.currentIndexChanged.connect(self._onQualityChanged)

    def _onQualityChanged(self, index: int):
        self.optionsChanged.emit()

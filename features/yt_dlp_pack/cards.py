from qfluentwidgets import ComboBox

from app.view.cards.draft_cards import UniversalDraftCard

QUALITY_TIERS = (
    ("bv*+ba/b", "Best"),
    ("bv*[height<=2160]+ba/b", "4K"),
    ("bv*[height<=1440]+ba/b", "1440p"),
    ("bv*[height<=1080]+ba/b", "1080p"),
    ("bv*[height<=720]+ba/b", "720p"),
    ("bv*[height<=480]+ba/b", "480p"),
)


class YtDlpDraftCard(UniversalDraftCard):

    def _initWidget(self):
        super()._initWidget()
        self.qualityCombo = ComboBox(self)
        self.qualityCombo.setMinimumWidth(120)
        for value, label in QUALITY_TIERS:
            self.qualityCombo.addItem(label, userData=value)
        self.qualityCombo.setCurrentIndex(0)

    def _initLayout(self):
        super()._initLayout()
        self.layout().addWidget(self.qualityCombo)

    def _bind(self):
        super()._bind()
        self.qualityCombo.currentIndexChanged.connect(self._onQualityChanged)

    def _onQualityChanged(self, _index: int):
        step = self._task.steps[0] if self._task.steps else None
        if step is not None:
            step.videoFormat = self.qualityCombo.currentData() or "bv*+ba/b"

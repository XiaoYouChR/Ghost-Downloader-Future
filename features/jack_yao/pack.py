from __future__ import annotations

import json
import sys
from base64 import b64decode
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QPainter, QPixmap
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget
from qfluentwidgets import (
    Action,
    BodyLabel,
    CaptionLabel,
    FluentIcon,
    IconWidget,
    MaskDialogBase,
    FluentStyleSheet,
    OptionsConfigItem,
    OptionsValidator,
    ComboBoxSettingCard,
    PixmapLabel,
    PlainTextEdit,
    PrimaryPushButton,
    PrimarySplitPushButton,
    PushButton,
    PushSettingCard,
    RangeConfigItem,
    RangeSettingCard,
    RangeValidator,
    RoundMenu,
    SettingCardGroup,
    SimpleCardWidget,
    TitleLabel,
    isDarkTheme,
)

from app.client import buildClient
from app.config.cfg import cfg
from app.models.pack import FeaturePack

if sys.platform != "darwin":
    from qfluentwidgets import SmoothScrollArea as ScrollArea
else:
    from qfluentwidgets import ScrollArea

CATALOG_API = "https://xineko-my.sharepoint.com/personal/os_store_xineko_onmicrosoft_com/_layouts/52/download.aspx?share=IQCK7kKU1-8oSqWDNNPss2xeAbmG3v4cItTXNqW2NG9Hzwc"


async def fetchCatalog() -> list[dict]:
    client = buildClient()
    try:
        response = await client.get(CATALOG_API)
        response.raise_for_status()
        return json.loads(await response.text())["OS"]
    finally:
        client.close()


class CatalogPage(ScrollArea):
    navIcon = FluentIcon.CLOUD_DOWNLOAD

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CatalogPage")
        self.navTitle = self.tr("资源下载")
        self._cards: list[CatalogCard] = []

        self._scrollWidget = QWidget()
        self._scrollWidget.setMinimumWidth(816)
        self._layout = QVBoxLayout(self._scrollWidget)
        self._loadingWidget = LoadingWidget(self._scrollWidget)

        self._initWidget()
        self._initLayout()
        self._bind()
        self._loadCatalog()

    def _initWidget(self):
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._layout.addWidget(self._loadingWidget, 0, Qt.AlignmentFlag.AlignCenter)

    def _initLayout(self):
        self.setWidget(self._scrollWidget)
        self.setWidgetResizable(True)
        self.enableTransparentBackground()

    def _bind(self):
        self._loadingWidget.retryRequested.connect(self._loadCatalog)

    def _loadCatalog(self):
        from app.services.coroutine_runner import coroutineRunner
        self._loadingWidget.setLoading()
        coroutineRunner.submit(fetchCatalog(), done=self._onCatalogLoaded, failed=self._onCatalogFailed)

    def _onCatalogLoaded(self, items: list[dict]):
        for card in self._cards:
            self._layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()

        for item in items:
            card = CatalogCard(item, self._scrollWidget)
            self._layout.addWidget(card)
            self._cards.append(card)

        self._layout.removeWidget(self._loadingWidget)
        self._loadingWidget.hide()

    def _onCatalogFailed(self, error: str):
        self._loadingWidget.setError(f"加载失败: {error}")


class LoadingWidget(QWidget):
    retryRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.iconWidget = IconWidget(FluentIcon.SYNC, self)
        self.label = CaptionLabel("正在加载...", self)
        self.retryButton = PushButton("重试", self)

        self.iconWidget.setFixedSize(64, 64)
        self.label.setTextColor(QColor(96, 96, 96), QColor(216, 216, 216))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)
        self.retryButton.setVisible(False)
        self.retryButton.clicked.connect(self._onRetry)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.addWidget(self.iconWidget, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.label, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.retryButton, 0, Qt.AlignmentFlag.AlignHCenter)

    def setLoading(self):
        self.iconWidget.setIcon(FluentIcon.SYNC)
        self.label.setText("正在加载...")
        self.retryButton.setVisible(False)
        self.show()

    def setError(self, text: str):
        self.iconWidget.setIcon(FluentIcon.CANCEL)
        self.label.setText(text)
        self.retryButton.setVisible(True)

    def _onRetry(self):
        self.retryRequested.emit()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(255, 255, 255, 13 if isDarkTheme() else 200))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)


class CatalogCard(SimpleCardWidget):
    def __init__(self, item: dict, parent=None):
        super().__init__(parent)
        self._catalogItems: list[dict] = item["List"]
        self._videoUrl: str = item["Video"]
        self.setFixedHeight(91)

        self.logoLabel = PixmapLabel(self)
        self.logoLabel.setFixedSize(71, 71)
        self.logoLabel.setScaledContents(True)
        self.logoLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pixmap = QPixmap()
        pixmap.loadFromData(b64decode(item["Icon"]))
        self.logoLabel.setPixmap(pixmap)
        self.logoLabel.setFixedSize(71, 71)

        self.titleLabel = TitleLabel(item["Name"], self)
        self.bodyLabel = BodyLabel(item["Intro"].replace(r"\n", "\n"), self)
        self.bodyLabel.setMaximumHeight(61)
        self.bodyLabel.setWordWrap(True)

        self.downloadButton = PrimarySplitPushButton(self)
        self.downloadButton.setFixedSize(121, 31)
        self.downloadButton.setText("      下载      ")

        self._menu = RoundMenu(parent=self)
        self._videoAction = Action(FluentIcon.VIDEO, "视频")
        self._menu.addAction(self._videoAction)
        self.downloadButton.setFlyout(self._menu)

        textLayout = QVBoxLayout()
        textLayout.setSpacing(0)
        textLayout.addWidget(self.titleLabel)
        textLayout.addWidget(self.bodyLabel)

        mainLayout = QHBoxLayout(self)
        mainLayout.setSpacing(12)
        mainLayout.addWidget(self.logoLabel)
        mainLayout.addLayout(textLayout)
        mainLayout.addWidget(self.downloadButton)

        self._videoAction.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(self._videoUrl)))
        self.downloadButton.clicked.connect(self._onDownloadClicked)

    def _onDownloadClicked(self):
        dialog = CatalogDownloadDialog(self.window(), self._catalogItems)
        dialog.exec()


class CatalogDownloadDialog(MaskDialogBase):
    def __init__(self, parent=None, catalogItems: list[dict] | None = None):
        super().__init__(parent)
        self._items = catalogItems or []
        self._folder = cfg.downloadFolder.value

        FluentStyleSheet.DIALOG.apply(self.widget)
        self.setShadowEffect(60, (0, 10), QColor(0, 0, 0, 50))
        self.setMaskColor(QColor(0, 0, 0, 76))
        self.widget.setMinimumSize(510, 580)
        self.widget.setMaximumSize(680, 580)

        versions = [item["Version"] for item in self._items]
        versionItem = OptionsConfigItem("Material", "Version", versions[0], OptionsValidator(versions))

        self._versionGroup = SettingCardGroup("选择版本", self.widget)
        self._versionCard = ComboBoxSettingCard(
            versionItem, FluentIcon.VIEW, "选择版本", "选择你想下载的版本",
            texts=versions, parent=self._versionGroup,
        )
        self._versionGroup.addSettingCard(self._versionCard)

        self._logGroup = SettingCardGroup("更新日志", self.widget)
        self._logEdit = PlainTextEdit(self._logGroup)
        self._logEdit.setReadOnly(True)
        self._logEdit.setMinimumHeight(140)
        self._logEdit.setPlainText(self._items[0]["Log"] if self._items else "")
        self._logEdit.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum))
        self._logGroup.addSettingCard(self._logEdit)

        self._settingGroup = SettingCardGroup("下载设置", self.widget)
        self._folderCard = PushSettingCard(
            "选择下载目录", FluentIcon.DOWNLOAD, "下载目录",
            self._folder, self._settingGroup,
        )
        self._subworkerItem = RangeConfigItem("Material", "SubworkerCount", cfg.preBlockNum.value, RangeValidator(1, 256))
        self._subworkerCard = RangeSettingCard(
            self._subworkerItem,
            FluentIcon.CHAT, "下载线程数", "下载线程越多，下载越快", self._settingGroup,
        )
        self._settingGroup.addSettingCards([self._folderCard, self._subworkerCard])

        self._cancelButton = PushButton("取消下载", self.widget)
        self._startButton = PrimaryPushButton("开始下载", self.widget)

        buttonLayout = QHBoxLayout()
        buttonLayout.setSpacing(18)
        buttonLayout.addWidget(self._cancelButton)
        buttonLayout.addWidget(self._startButton)

        mainLayout = QVBoxLayout(self.widget)
        mainLayout.setContentsMargins(18, 18, 18, 18)
        mainLayout.addWidget(self._versionGroup)
        mainLayout.addWidget(self._logGroup)
        mainLayout.addWidget(self._settingGroup)
        mainLayout.addLayout(buttonLayout)

        self._folderCard.clicked.connect(self._onFolderClicked)
        self._cancelButton.clicked.connect(self.close)
        self._startButton.clicked.connect(self._onStartClicked)
        self._versionCard.comboBox.currentIndexChanged.connect(
            lambda i: self._logEdit.setPlainText(self._items[i]["Log"] if i < len(self._items) else "")
        )

    def _onFolderClicked(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹", self._folder)
        if folder:
            self._folder = folder
            self._folderCard.setContent(folder)

    def _onStartClicked(self):
        from qfluentwidgets import InfoBar, InfoBarPosition
        from app.models.task import ResourceTaskOptions
        from app.services.coroutine_runner import coroutineRunner
        from app.services.feature_service import featureService
        from app.services.task_service import taskService

        index = self._versionCard.comboBox.currentIndex()
        item = self._items[index]
        outputFolder = Path(self._folder)
        subworkerCount = self._subworkerItem.value
        window = self.window()

        def onParsed(task):
            for step in task.steps:
                step.setOptions({"subworkerCount": subworkerCount})
            taskService.add(task)

        def onFailed(error):
            InfoBar.error("下载失败", str(error), duration=-1,
                          position=InfoBarPosition.BOTTOM_RIGHT, parent=window)

        coroutineRunner.submit(
            featureService.parse(ResourceTaskOptions(url=item["Url"], outputFolder=outputFolder)),
            done=onParsed,
            failed=onFailed,
        )
        self.close()


class JackYaoPack(FeaturePack):
    packId = "jack_yao"

    def pages(self):
        return [CatalogPage()]

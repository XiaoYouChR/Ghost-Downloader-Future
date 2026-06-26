from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from PySide6.QtCore import QUrl, QTimer, Qt
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtWidgets import QApplication
from qfluentwidgets import (
    MSFluentWindow, FluentIcon, NavigationItemPosition, MessageBox, Theme, InfoBar, InfoBarPosition,
)

from app.config.cfg import cfg
from app.config.constants import FEEDBACK_URL
from app.services.task_draft import TaskDraft
from app.services.task_service import taskService
from app.signal_bus import signalBus
from app.view.dialogs.task_draft import TaskDraftDialog
from app.view.pages.setting_page import SettingPage
from app.view.pages.task_page import TaskPage

if TYPE_CHECKING:
    from app.models.task import Task


class MainWindow(MSFluentWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.taskPage = TaskPage(self)
        self.settingPage = SettingPage(self)

        self._draft = TaskDraft(parent=self)
        self._draft.taskConfirmed.connect(taskService.add)
        self._draftDialog = TaskDraftDialog(self._draft, parent=self)

        self._geometryApplied = False

        self._initWidget()
        self._initLayout()
        self._bind()

    def _initWidget(self) -> None:
        self.setWindowIcon(QIcon(":/image/logo.png"))
        self.setWindowTitle("Ghost Downloader")
        self.setMinimumSize(960, 540)
        if sys.platform == "darwin":
            self.titleBar.hBoxLayout.insertSpacing(0, 60)

    def _initLayout(self) -> None:
        from app.services.feature_service import featureService

        self.addSubInterface(self.taskPage, FluentIcon.DOWNLOAD, self.tr("下载任务"),
                             position=NavigationItemPosition.TOP)
        self.navigationInterface.addItem(
            routeKey="addTaskButton",
            text=self.tr("新建任务"),
            selectable=False,
            icon=FluentIcon.ADD,
            onClick=lambda: self.addUrls([]),
            position=NavigationItemPosition.TOP,
        )
        for page in featureService.pages():
            self.addSubInterface(page, page.navIcon, page.navTitle,
                                 position=NavigationItemPosition.TOP)
        self.addSubInterface(self.settingPage, FluentIcon.SETTING, self.tr("设置"),
                             position=NavigationItemPosition.BOTTOM)

    def _bind(self) -> None:
        cfg.customThemeMode.valueChanged.connect(self._setTheme)
        QApplication.instance().styleHints().colorSchemeChanged.connect(self._onSystemColorSchemeChanged)
        signalBus.updateAvailable.connect(self._onUpdateAvailable)

        if sys.platform == "win32":
            cfg.backgroundEffect.valueChanged.connect(self._setBackgroundEffect)

    def addUrls(self, urls: list[str]) -> None:
        if urls:
            self._draftDialog.addUrls(urls)
        if not self._draftDialog.isVisible():
            self._draftDialog.showMask()

    def addTasks(self, tasks: list[Task]) -> None:
        self._draftDialog.addParsedTasks(tasks)
        if self._draftDialog.isVisible():
            return
        if sys.platform == "darwin":
            from app.platform.desktop import raiseWindow
            raiseWindow(self)
            self._draftDialog.showMask()
        else:
            self._draftDialog.showStandalone()

    def confirmPair(self, request) -> None:
        from app.services.browser_service import browserService

        session = request["session"]
        requestId = request["requestId"]
        peerAddress = request.get("peerAddress", "")
        extensionVersion = request.get("extensionVersion", self.tr("未知"))
        clientKind = request.get("clientKind", self.tr("浏览器扩展"))

        content = self.tr(
            "浏览器扩展正在请求连接到 Ghost Downloader。\n\n"
            "来源: {0}\n客户端: {1}\n扩展版本: {2}\n\n"
            "仅在你刚刚点击扩展里的\"自动配对\"时允许。"
        ).format(peerAddress, clientKind, extensionVersion)

        dialog = MessageBox(self.tr("浏览器扩展配对请求"), content, self)
        dialog.yesButton.setText(self.tr("允许配对"))
        dialog.cancelButton.setText(self.tr("拒绝"))
        dialog.contentLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        if dialog.exec():
            browserService.approvePair(session, requestId)
        else:
            browserService.rejectPair(session, requestId)

    def _onUpdateAvailable(self, release) -> None:
        from qfluentwidgets import PrimaryPushButton
        from app.view.dialogs.release_info import ReleaseInfoDialog

        infoBar = InfoBar(
            icon=FluentIcon.CLOUD,
            title=self.tr("检测到新版本"),
            content=self.tr("最新版本: {0}").format(release.version),
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            duration=-1,
            position=InfoBarPosition.BOTTOM_RIGHT,
            parent=self,
        )
        detailButton = PrimaryPushButton(FluentIcon.CHAT, self.tr("查看详情"))
        detailButton.clicked.connect(lambda: ReleaseInfoDialog(release, self).exec())
        infoBar.addWidget(detailButton)
        infoBar.show()

    def alertException(self, message: str) -> None:
        dialog = MessageBox(
            self.tr("程序发生异常"),
            self.tr("点击\"确定\"后将复制错误信息并打开反馈页面。\n\n{0}").format(message),
            self,
        )
        if dialog.exec():
            QApplication.clipboard().setText(message)
            QDesktopServices.openUrl(QUrl(FEEDBACK_URL))

    def closeEvent(self, event) -> None:
        event.ignore()
        if sys.platform == "darwin" and self.isFullScreen():
            self.showNormal()
            QTimer.singleShot(1000, self.hide)
            return
        if not self.isMaximized():
            cfg.set(cfg.geometry, self.geometry())
        self.hide()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._geometryApplied:
            self._geometryApplied = True
            saved = cfg.geometry.value
            if saved.isValid() and QApplication.screenAt(saved.center()) is not None:
                self.setGeometry(saved)
            else:
                self.resize(960, 540)
                desktop = QApplication.primaryScreen().availableGeometry()
                self.move(desktop.center() - self.rect().center())

    def nativeEvent(self, eventType, message):
        if sys.platform == "win32" and eventType == "windows_generic_MSG":
            from ctypes.wintypes import MSG
            from app.platform.application import WM_USER_WAKE, WM_COPYDATA, fileUrisFromCopyData
            msg = MSG.from_address(message.__int__())

            if msg.message == WM_USER_WAKE:
                from app.platform.desktop import raiseWindow
                raiseWindow(self)
                return True, 0

            if msg.message == WM_COPYDATA:
                uris = fileUrisFromCopyData(msg.lParam)
                if uris:
                    signalBus.openFileRequested.emit(uris)
                return True, 1

        return super().nativeEvent(eventType, message)

    def _setTheme(self, value) -> None:
        from qfluentwidgets import setTheme, Theme
        setTheme(value if isinstance(value, Theme) else Theme.AUTO, save=False)
        if sys.platform == "win32":
            self._refreshBackgroundEffect()

    def _onSystemColorSchemeChanged(self, scheme) -> None:
        if cfg.customThemeMode.value != Theme.AUTO:
            return
        self._setTheme(Theme.AUTO)

    def _refreshBackgroundEffect(self) -> None:
        if sys.platform == "win32":
            self._setBackgroundEffect(cfg.backgroundEffect.value)

    def _setBackgroundEffect(self, value) -> None:
        if sys.platform != "win32":
            return
        from qfluentwidgets import isDarkTheme
        self.windowEffect.removeBackgroundEffect(self.winId())
        isDark = isDarkTheme()

        if value == "Acrylic":
            self.setStyleSheet("background-color: transparent")
            self.windowEffect.setAcrylicEffect(self.winId(), "00000030" if isDark else "FFFFFF30")
        elif value in {"Mica", "MicaBlur"}:
            self.setStyleSheet("background-color: transparent")
            self.windowEffect.setMicaEffect(self.winId(), isDark)
        elif value == "MicaAlt":
            self.setStyleSheet("background-color: transparent")
            self.windowEffect.setMicaEffect(self.winId(), isDark, isAlt=True)
        elif value == "Aero":
            self.setStyleSheet("background-color: transparent")
            self.windowEffect.setAeroEffect(self.winId())
        elif value == "None":
            self.setStyleSheet("")

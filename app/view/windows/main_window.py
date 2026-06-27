from __future__ import annotations

import sys
import weakref
from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent, QRect, QUrl, QTimer, Qt
from PySide6.QtGui import QColor, QIcon, QDesktopServices, QPalette
from PySide6.QtWidgets import QApplication, QHBoxLayout
from qfluentwidgets import (
    MSFluentWindow, FluentIcon, NavigationItemPosition, MessageBox, Theme, InfoBar, InfoBarPosition,
    setThemeColor,
)

from app.config.cfg import cfg
from app.config.constants import AUTHOR_URL, FEEDBACK_URL
from app.services.task_draft import TaskDraft
from app.services.task_service import taskService
from app.signal_bus import signalBus
from app.view.pages.task_page import TaskPage

if TYPE_CHECKING:
    from app.models.task import Task
    from app.view.dialogs.task_draft import TaskDraftDialog
    from app.view.pages.setting_page import SettingPage


class MainWindow(MSFluentWindow):

    def __init__(self, parent=None):
        self._isGeometryRestored = False
        self._isBackgroundEffectDirty = False
        super().__init__(parent)
        self.setMicaEffectEnabled(False)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.taskPage = TaskPage(self)
        self.settingPage: SettingPage | None = None

        self._draft = TaskDraft(parent=self)
        self._draft.taskConfirmed.connect(taskService.add)
        self._draftDialog: TaskDraftDialog | None = None

        self._packPages: dict[type, object] = {}

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
        for PageClass in featureService.pages():
            self.navigationInterface.addItem(
                routeKey=PageClass.__name__,
                text=PageClass.title,
                icon=PageClass.icon,
                onClick=lambda _, cls=PageClass: self._showPackPage(cls),
                position=NavigationItemPosition.TOP,
            )
        self.navigationInterface.addItem(
            routeKey="SettingPage",
            text=self.tr("设置"),
            icon=FluentIcon.SETTING,
            onClick=self._showSettingPage,
            position=NavigationItemPosition.BOTTOM,
        )

    def systemTitleBarRect(self, size) -> QRect:
        return QRect(0, 10, 75, size.height())

    def _normalBackgroundColor(self):
        from qfluentwidgets import isDarkTheme
        if self.styleSheet() == "":
            return self._darkBackgroundColor if isDarkTheme() else self._lightBackgroundColor
        return QColor(0, 0, 0, 0)

    def _showPackPage(self, pageClass: type) -> None:
        page = self._packPages.get(pageClass)
        if page is None:
            page = pageClass(self)
            self.addSubInterface(page, pageClass.icon, pageClass.title,
                                 position=NavigationItemPosition.TOP)
            self._packPages[pageClass] = page
        self.switchTo(page)

    def _showSettingPage(self) -> None:
        if self.settingPage is None:
            from app.view.pages.setting_page import SettingPage

            self.settingPage = SettingPage(self)
            self.settingPage.setProperty("isStackedTransparent", False)
            self.stackedWidget.addWidget(self.settingPage)
        self.switchTo(self.settingPage)

    def _bind(self) -> None:
        cfg.customThemeMode.valueChanged.connect(self._onUserThemeChanged)
        QApplication.instance().styleHints().colorSchemeChanged.connect(self._onSystemColorSchemeChanged)

        if sys.platform == "win32":
            cfg.backgroundEffect.valueChanged.connect(self._setBackgroundEffect)
        if sys.platform == "darwin":
            from PySide6.QtGui import QKeySequence, QShortcut
            QShortcut(QKeySequence.StandardKey.Close, self).activated.connect(self.close)

    def addUrls(self, urls: list[str]) -> None:
        dialog = self._taskDraftDialog()
        if urls:
            dialog.addUrls(urls)
        if not dialog.isVisible():
            dialog.showMask()

    def addTasks(self, tasks: list[Task]) -> None:
        dialog = self._taskDraftDialog()
        dialog.addParsedTasks(tasks)
        if dialog.isVisible():
            return
        if sys.platform == "darwin":
            from app.platform.desktop import raiseWindow
            raiseWindow(self)
            dialog.showMask()
        else:
            dialog.showStandalone()

    def _taskDraftDialog(self) -> TaskDraftDialog:
        if self._draftDialog is None:
            from app.view.dialogs.task_draft import TaskDraftDialog

            self._draftDialog = TaskDraftDialog(self._draft, parent=self)
        return self._draftDialog

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
        from qfluentwidgets import PrimaryPushButton, PushButton
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
        downloadButton = PrimaryPushButton(FluentIcon.DOWNLOAD, self.tr("立即下载"))
        downloadButton.clicked.connect(lambda: self._onDownloadUpdateClicked(release))
        infoBar.addWidget(downloadButton)
        detailButton = PushButton(FluentIcon.CHAT, self.tr("查看详情"))
        detailButton.clicked.connect(lambda: ReleaseInfoDialog(release, self).exec())
        infoBar.addWidget(detailButton)
        sponsorButton = PushButton(FluentIcon.HEART, self.tr("请作者喝咖啡"))
        sponsorButton.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(AUTHOR_URL)))
        infoBar.addWidget(sponsorButton)
        infoBar.show()

    def _onDownloadUpdateClicked(self, release) -> None:
        from app.models.task import TaskOptions
        from app.services.coroutine_runner import coroutineRunner
        from app.services.feature_service import featureService
        from app.update import bestAsset

        asset = bestAsset(release)
        if asset is None:
            InfoBar.warning(
                self.tr("未找到适配的安装包"),
                self.tr("请在版本详情中手动选择"),
                duration=3000, position=InfoBarPosition.BOTTOM_RIGHT, parent=self,
            )
            from app.view.dialogs.release_info import ReleaseInfoDialog
            ReleaseInfoDialog(release, self).exec()
            return

        windowRef = weakref.ref(self)

        def onParseFailed(error: str) -> None:
            from shiboken6 import isValid

            window = windowRef()
            if window is None or not isValid(window):
                return
            InfoBar.error(
                window.tr("创建下载任务失败"), str(error),
                duration=3000, position=InfoBarPosition.BOTTOM_RIGHT, parent=window,
            )

        coroutineRunner.submit(
            featureService.parse(TaskOptions(url=asset.downloadUrl)),
            done=lambda task: taskService.add(task),
            failed=onParseFailed,
        )

    def alertException(self, message: str) -> None:
        from qfluentwidgets import TransparentToolButton, ToolTipFilter

        dialog = MessageBox(
            self.tr("程序发生异常"),
            self.tr("点击\"确定\"后将复制错误信息并打开反馈页面。\n\n{0}").format(message),
            self,
        )
        logButton = TransparentToolButton(FluentIcon.DOCUMENT, dialog)
        logButton.setToolTip(self.tr("查看日志"))
        logButton.installEventFilter(ToolTipFilter(logButton))
        logButton.clicked.connect(self._openLogFolder)

        titleLayout = dialog.textLayout
        titleLayout.removeWidget(dialog.titleLabel)
        titleRow = QHBoxLayout()
        titleRow.addWidget(dialog.titleLabel, 1)
        titleRow.addWidget(logButton)
        titleLayout.insertLayout(0, titleRow)

        if dialog.exec():
            QApplication.clipboard().setText(message)
            QDesktopServices.openUrl(QUrl(FEEDBACK_URL))

    def _openLogFolder(self) -> None:
        from app.config.paths import APP_DATA_DIR
        from app.platform.desktop import openFolder
        openFolder(APP_DATA_DIR)

    def closeEvent(self, event) -> None:
        if sys.platform == "darwin" and self.isFullScreen():
            event.ignore()
            self.showNormal()
            QTimer.singleShot(1000, self.close)
            return
        if not self.isMaximized():
            cfg.set(cfg.geometry, self.geometry())
        self._draft.clear()
        self._cancelPendingViewWork()
        self._releaseNavigationHistory()
        event.accept()

    def _cancelPendingViewWork(self) -> None:
        if self.settingPage is not None:
            self.settingPage.cancelPendingWork()
        for page in self._packPages.values():
            cancelPendingWork = getattr(page, "cancelPendingWork", None)
            if callable(cancelPendingWork):
                cancelPendingWork()

    def _releaseNavigationHistory(self) -> None:
        from qfluentwidgets.common.router import qrouter

        stackedWidget = self.stackedWidget
        qrouter.history = [item for item in qrouter.history if item.stacked is not stackedWidget]
        for registered in list(qrouter.stackHistories):
            if registered is stackedWidget:
                qrouter.stackHistories.pop(registered, None)
                break
        qrouter.emptyChanged.emit(not bool(qrouter.history))

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._isGeometryRestored:
            self._isGeometryRestored = True
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

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.PaletteChange:
            self._refreshThemeColor()
        if self._isBackgroundEffectDirty and event.type() == QEvent.Type.ThemeChange:
            self._isBackgroundEffectDirty = False
            self._refreshBackgroundEffect()

    def _refreshThemeColor(self) -> None:
        palette = QApplication.palette()
        for role in (QPalette.ColorRole.Accent, QPalette.ColorRole.Highlight):
            color = palette.color(role)
            if color.isValid() and cfg.themeColor.value != color:
                setThemeColor(color, save=False)
                return

    def _onUserThemeChanged(self, value) -> None:
        self._setTheme(value, isUserTriggered=True)

    def _setTheme(self, value, isUserTriggered=False) -> None:
        from qfluentwidgets import setTheme
        setTheme(value if isinstance(value, Theme) else Theme.AUTO, save=False)
        if (
            not isUserTriggered
            and sys.platform == "win32"
            and cfg.backgroundEffect.value in {"Mica", "MicaBlur", "MicaAlt"}
        ):
            self._isBackgroundEffectDirty = True
            return
        self._isBackgroundEffectDirty = False
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


if sys.platform == "win32":
    from app.platform.windows import isWin10

    if isWin10():
        from ctypes import pointer
        from qframelesswindow import FramelessWindow, WindowEffect
        from qframelesswindow.windows.c_structures import ACCENT_STATE, WINDOWCOMPOSITIONATTRIB

        def _resetAcrylicEffect(self, hWnd):
            hWnd = int(hWnd)
            self.accentPolicy.AccentState = ACCENT_STATE.ACCENT_ENABLE_TRANSPARENTGRADIENT.value
            self.winCompAttrData.Attribute = WINDOWCOMPOSITIONATTRIB.WCA_ACCENT_POLICY.value
            self.SetWindowCompositionAttribute(hWnd, pointer(self.winCompAttrData))

        def _win10NativeEvent(self, eventType, message):
            if eventType == "windows_generic_MSG":
                from ctypes.wintypes import MSG
                from app.platform.application import WM_USER_WAKE, WM_COPYDATA, fileUrisFromCopyData
                msg = MSG.from_address(message.__int__())

                WM_ENTERSIZEMOVE = 561
                WM_EXITSIZEMOVE = 562
                if msg.message == WM_ENTERSIZEMOVE and cfg.backgroundEffect.value == "Acrylic":
                    self.windowEffect.resetAcrylicEffect(self.winId())
                elif msg.message == WM_EXITSIZEMOVE and cfg.backgroundEffect.value == "Acrylic":
                    from qfluentwidgets import isDarkTheme
                    self.windowEffect.setAcrylicEffect(
                        self.winId(), "00000030" if isDarkTheme() else "FFFFFF30",
                    )
                elif msg.message == WM_USER_WAKE:
                    from app.platform.desktop import raiseWindow
                    raiseWindow(self)
                    return True, 0
                elif msg.message == WM_COPYDATA:
                    uris = fileUrisFromCopyData(msg.lParam)
                    if uris:
                        signalBus.openFileRequested.emit(uris)
                    return True, 1

            return FramelessWindow.nativeEvent(self, eventType, message)

        WindowEffect.resetAcrylicEffect = _resetAcrylicEffect
        MainWindow.nativeEvent = _win10NativeEvent

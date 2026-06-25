import sys
from enum import Enum

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QSystemTrayIcon
from qfluentwidgets import (
    Action, FluentIcon, FluentIconBase, RoundMenu, Theme,
    getIconColor, isDarkTheme,
)

from app.services.task_service import taskService
from app.signal_bus import signalBus


class GhostIcon(FluentIconBase, Enum):
    GHOST = "ghost"

    def path(self, theme=Theme.AUTO) -> str:
        return ":/image/logo_menubar_template.png"

    def _toPixmap(self, theme: Theme) -> QPixmap:
        pixmap = QPixmap(self.path())
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor(getIconColor(theme)))
        painter.end()
        return pixmap

    def icon(self, theme=Theme.AUTO, color=None) -> QIcon:
        return QIcon(self._toPixmap(theme))

    def render(self, painter, rect, theme=Theme.AUTO, indexes=None, **attributes) -> None:
        painter.drawPixmap(QRectF(rect).toRect(), self._toPixmap(theme))


if sys.platform == "win32":
    from PySide6.QtWidgets import QProxyStyle, QStyle, QStyleFactory
    from qframelesswindow import WindowEffect

    class MenuStyle(QProxyStyle):

        def __init__(self, iconSize=14):
            super().__init__()
            self._iconSize = iconSize

        def pixelMetric(self, metric, option, widget):
            if metric == QStyle.PixelMetric.PM_SmallIconSize:
                return self._iconSize
            return super().pixelMetric(metric, option, widget)

        def polish(self, app, /):
            QStyleFactory.create("fusion").polish(app)

        def unpolish(self, app, /):
            QStyleFactory.create("fusion").polish(app)

    class AcrylicMenu(RoundMenu):

        def __init__(self, title="", parent=None):
            super().__init__(title, parent)
            self._windowEffect = WindowEffect(self)
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.NoDropShadowWindowHint)
            self.setStyle(MenuStyle())
            self.view.setProperty("transparent", True)

        def showEvent(self, event) -> None:
            self._windowEffect.addMenuShadowEffect(self.winId())
            self._windowEffect.enableBlurBehindWindow(self.winId())
            self._windowEffect.setAcrylicEffect(
                self.winId(),
                "00000030" if isDarkTheme() else "FFFFFF30",
            )
            super().showEvent(event)

        def paintEvent(self, e) -> None:
            painter = QPainter(self)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 1))
            painter.drawRect(self.rect())

    TrayMenu = AcrylicMenu
else:
    TrayMenu = RoundMenu


class SystemTrayIcon(QSystemTrayIcon):

    def __init__(self, icon: QIcon, parent=None):
        super().__init__(icon, parent)
        self.setToolTip("Ghost Downloader")

        menu = TrayMenu(parent=self)
        menu.addAction(Action(GhostIcon.GHOST, self.tr("仪表盘"), self,
                              triggered=lambda: signalBus.activationRequested.emit()))
        menu.addAction(Action(FluentIcon.PLAY, self.tr("全部开始"), self,
                              triggered=taskService.startAll))
        menu.addAction(Action(FluentIcon.PAUSE, self.tr("全部暂停"), self,
                              triggered=taskService.pauseAll))
        menu.addSeparator()
        menu.addAction(Action(FluentIcon.CLOSE, self.tr("退出程序"), self,
                              triggered=QApplication.instance().quit))
        self.setContextMenu(menu)

        self.activated.connect(self._onActivated)

    def _onActivated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            signalBus.activationRequested.emit()

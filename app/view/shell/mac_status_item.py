from PySide6.QtCore import QCoreApplication, QResource
from PySide6.QtWidgets import QApplication

from AppKit import (
    NSObject,
    NSStatusBar,
    NSVariableStatusItemLength,
    NSImage,
    NSImageLeft,
    NSMenu,
    NSMenuItem,
)
from Foundation import NSData

from app.config.cfg import cfg
from app.format import toReadableSize
from app.signal_bus import signalBus


def tr(text: str) -> str:
    return QCoreApplication.translate("SystemTrayIcon", text)


class MenuTarget(NSObject):
    def showDashboard_(self, sender):
        signalBus.activationRequested.emit()

    def startAll_(self, sender):
        from app.services.task_service import taskService
        taskService.startAll()

    def pauseAll_(self, sender):
        from app.services.task_service import taskService
        taskService.pauseAll()

    def quitApp_(self, sender):
        QApplication.instance().quit()


class MacStatusItem:
    ICON_SIZE = 16

    def __init__(self):
        self._statusItem = NSStatusBar.systemStatusBar().statusItemWithLength_(
            NSVariableStatusItemLength
        )
        self._button = self._statusItem.button()
        self._button.setImage_(self._toMenuBarIcon())
        self._button.setImagePosition_(NSImageLeft)

        self._target = MenuTarget.alloc().init()
        self._statusItem.setMenu_(self._buildMenu())

        cfg.shouldShowMenuBarSpeed.valueChanged.connect(self._onShowSpeedChanged)

    def show(self) -> None:
        self._statusItem.setVisible_(True)

    def setSpeed(self, bytesPerSecond: int) -> None:
        if cfg.shouldShowMenuBarSpeed.value and bytesPerSecond > 0:
            self._button.setTitle_(f" {toReadableSize(bytesPerSecond)}/s")
        else:
            self._button.setTitle_("")

    def _buildMenu(self) -> NSMenu:
        menu = NSMenu.alloc().init()
        menu.setAutoenablesItems_(False)
        for title, selector in (
            (tr("仪表盘"), "showDashboard:"),
            (tr("全部开始"), "startAll:"),
            (tr("全部暂停"), "pauseAll:"),
            (tr("退出程序"), "quitApp:"),
        ):
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, selector, "")
            item.setTarget_(self._target)
            menu.addItem_(item)
        return menu

    def _toMenuBarIcon(self) -> NSImage:
        raw = QResource(":/image/logo_menubar_template.png").data()
        image = NSImage.alloc().initWithData_(NSData.dataWithBytes_length_(raw, len(raw)))
        size = image.size()
        image.setSize_((self.ICON_SIZE * size.width / size.height, self.ICON_SIZE))
        image.setTemplate_(True)
        return image

    def _onShowSpeedChanged(self, enabled: bool) -> None:
        if not enabled:
            self._button.setTitle_("")

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from app.services.task_service import taskService
from app.signal_bus import signalBus


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, icon: QIcon, parent=None):
        super().__init__(icon, parent)
        self.setToolTip("Ghost Downloader")

        menu = QMenu()
        menu.addAction(QAction(self.tr("仪表盘"), self, triggered=lambda: signalBus.activationRequested.emit()))
        menu.addAction(QAction(self.tr("全部开始"), self, triggered=taskService.startAll))
        menu.addAction(QAction(self.tr("全部暂停"), self, triggered=taskService.pauseAll))
        menu.addSeparator()
        menu.addAction(QAction(self.tr("退出程序"), self, triggered=QApplication.instance().quit))
        self.setContextMenu(menu)

        self.activated.connect(self._onActivated)

    def _onActivated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            signalBus.activationRequested.emit()

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QSystemTrayIcon


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, icon: QIcon, parent=None):
        super().__init__(icon, parent)

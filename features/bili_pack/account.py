from PySide6.QtCore import QObject, Signal


class BilibiliAccount(QObject):
    accountChanged = Signal()
    qrStateChanged = Signal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._username = ""

    @property
    def cookie(self) -> str:
        from .config import bilibiliConfig
        return bilibiliConfig.userCookie.value

    @property
    def isLoggedIn(self) -> bool:
        return bool(self.cookie)

    @property
    def username(self) -> str:
        return self._username

    def startQrLogin(self): ...

    def cancelQrLogin(self): ...

    def setCookie(self, cookie: str): ...

    def logout(self): ...

    def fetchAccountInfo(self): ...


bilibiliAccount = BilibiliAccount()

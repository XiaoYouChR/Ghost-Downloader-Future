from PySide6.QtWidgets import QWidget

from app.config.cfg import ConfigItem
from app.models.pack import PackConfig
from qfluentwidgets import (
    BoolValidator,
    MessageBoxBase,
    OptionsConfigItem,
    OptionsValidator,
    SettingCard,
)


class ScanLoginDialog(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)

    def _initWidget(self): ...
    def _initLayout(self): ...
    def _bind(self): ...

    def reloadQrCode(self): ...


class EditCookieDialog(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)

    def _initWidget(self): ...
    def _initLayout(self): ...


class BilibiliLoginSettingCard(SettingCard):
    def __init__(self, parent=None):
        super().__init__(parent)

    def _initLayout(self): ...
    def _bind(self): ...

    def refreshLoginInfo(self): ...
    def _setButtonsEnabled(self, enabled: bool): ...
    def _onScanLogin(self): ...
    def _onEditCookie(self): ...
    def _onLogout(self): ...


class CookieValidator:
    def validate(self, value) -> bool: ...
    def correct(self, value) -> str: ...


class BilibiliConfig(PackConfig):
    userCookie = ConfigItem("Bilibili", "UserCookie", "")
    defaultQuality = OptionsConfigItem(
        "Bilibili", "DefaultQuality", 80,
        OptionsValidator([16, 32, 64, 80, 112, 116, 120, 125, 126, 127, 128]),
    )
    alternativeQuality = OptionsConfigItem(
        "Bilibili", "AlternativeQuality", "max",
        OptionsValidator(["max", "min"]),
    )
    parseHDR = ConfigItem("Bilibili", "ParseHDR", False, BoolValidator())
    parseDolby = ConfigItem("Bilibili", "ParseDolby", False, BoolValidator())

    def setupSettings(self, settingPage): ...


bilibiliConfig = BilibiliConfig()

from PySide6.QtCore import Qt

from qfluentwidgets import (
    BoolValidator,
    BodyLabel,
    CaptionLabel,
    ConfigItem,
    FluentIcon,
    MessageBoxBase,
    OptionsConfigItem,
    OptionsValidator,
    PlainTextEdit,
    PrimaryPushButton,
    PushButton,
    SettingCard,
    SubtitleLabel,
)

from app.config.cfg import ConfigItem
from app.models.pack import PackConfig
from .account import bilibiliAccount, toCookie
class ScanLoginDialog(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setClosableOnMaskClicked(True)
        self.widget.setFixedSize(430, 560)
        self.yesButton.hide()
        self.cancelButton.setText(self.tr("关闭"))

        self.titleLabel = SubtitleLabel(self.tr("扫码登录"), self.widget)
        self.statusLabel = BodyLabel(self.tr("正在获取二维码..."), self.widget)
        self.statusLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.statusLabel.setWordWrap(True)

        self._initWidget()
        self._initLayout()
        self._bind()
        self.reloadQrCode()

    def _initWidget(self):
        self.refreshButton = PrimaryPushButton(FluentIcon.SYNC, self.tr("刷新二维码"), self.widget)

    def _initLayout(self):
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(12)
        self.viewLayout.addWidget(self.statusLabel)
        self.viewLayout.addSpacing(6)
        self.viewLayout.addWidget(self.refreshButton, 0, Qt.AlignmentFlag.AlignCenter)

    def _bind(self):
        self.refreshButton.clicked.connect(self.reloadQrCode)
        bilibiliAccount.qrStateChanged.connect(self._onQrState)

    def reloadQrCode(self):
        self.statusLabel.setText(self.tr("正在获取二维码..."))
        bilibiliAccount.startQrLogin()

    def _onQrState(self, statusCode: int, text: str):
        from .account import QR_UNSCANNED, QR_SCANNED
        if statusCode == 0:
            self.statusLabel.setText(text)
        elif statusCode == QR_UNSCANNED:
            self.statusLabel.setText(self.tr("等待扫码"))
        elif statusCode == QR_SCANNED:
            self.statusLabel.setText(self.tr("二维码已扫码，请在手机端确认登录"))
        else:
            self.statusLabel.setText(text or str(statusCode))

    def done(self, code):
        bilibiliAccount.cancelQrLogin()
        super().done(code)
class EditCookieDialog(MessageBoxBase):
    def __init__(self, parent=None, initialCookie: str = ""):
        super().__init__(parent)
        self.setClosableOnMaskClicked(True)

        self._initWidget(initialCookie)
        self._initLayout()

    def _initWidget(self, initialCookie: str = ""):
        self.widget.setFixedSize(420, 500)
        self.yesButton.setText(self.tr("保存"))
        self.cancelButton.setText(self.tr("取消"))
        self.titleLabel = SubtitleLabel(self.tr("手动导入 Cookie"), self.widget)
        self.descriptionLabel = CaptionLabel(
            self.tr("请粘贴浏览器导出的完整 Cookie，留空后保存可清空当前 Cookie"), self.widget,
        )
        self.cookieTextEdit = PlainTextEdit(self.widget)
        self.cookieTextEdit.setPlaceholderText(self.tr("请在此输入用户 Cookie"))
        self.cookieTextEdit.setPlainText(initialCookie or "")

    def _initLayout(self):
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.descriptionLabel)
        self.viewLayout.addWidget(self.cookieTextEdit)
class BilibiliLoginSettingCard(SettingCard):
    def __init__(self, parent=None):
        super().__init__(
            FluentIcon.VIEW, self.tr("账号登录"),
            self.tr("状态：未登录"), parent,
        )
        self.scanButton = PrimaryPushButton(self.tr("扫码登录"), self)
        self.editButton = PushButton(self.tr("导入 Cookie"), self)
        self.logoutButton = PushButton(self.tr("退出登录"), self)

        self._initLayout()
        self._bind()
        self.refreshLoginInfo()

    def _initLayout(self):
        self.hBoxLayout.addWidget(self.scanButton, 0)
        self.hBoxLayout.addSpacing(8)
        self.hBoxLayout.addWidget(self.editButton, 0)
        self.hBoxLayout.addSpacing(8)
        self.hBoxLayout.addWidget(self.logoutButton, 0)
        self.hBoxLayout.addSpacing(16)

    def _bind(self):
        self.scanButton.clicked.connect(self._onScanLogin)
        self.editButton.clicked.connect(self._onEditCookie)
        self.logoutButton.clicked.connect(self._onLogout)
        bilibiliAccount.accountChanged.connect(self.refreshLoginInfo)

    def refreshLoginInfo(self):
        if bilibiliAccount.isLoggedIn:
            name = bilibiliAccount.username or self.tr("已登录")
            self.setContent(self.tr("状态：已登录 · {0}").format(name))
        else:
            self.setContent(self.tr("状态：未登录"))
        self.logoutButton.setEnabled(bilibiliAccount.isLoggedIn)

    def _setButtonsEnabled(self, enabled: bool):
        self.scanButton.setEnabled(enabled)
        self.editButton.setEnabled(enabled)
        self.logoutButton.setEnabled(enabled and bilibiliAccount.isLoggedIn)

    def _onScanLogin(self):
        dialog = ScanLoginDialog(self.window())
        dialog.exec()
        dialog.deleteLater()
        self.refreshLoginInfo()

    def _onEditCookie(self):
        dialog = EditCookieDialog(self.window(), bilibiliAccount.cookie)
        if dialog.exec():
            cookie = toCookie(dialog.cookieTextEdit.toPlainText())
            bilibiliAccount.setCookie(cookie)
        dialog.deleteLater()

    def _onLogout(self):
        self._setButtonsEnabled(False)
        bilibiliAccount.logout()
class CookieValidator:
    def validate(self, value) -> bool:
        return isinstance(value, str)

    def correct(self, value) -> str:
        return str(value) if isinstance(value, str) else ""
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
    shouldIncludeHdr = ConfigItem("Bilibili", "ParseHDR", False, BoolValidator())
    shouldIncludeDolby = ConfigItem("Bilibili", "ParseDolby", False, BoolValidator())

    def setupSettings(self, settingPage):
        from qfluentwidgets import ComboBoxSettingCard, FluentIcon, SwitchSettingCard
        from app.view.components.setting_card_group import CollapsibleSettingCardGroup

        self.biliGroup = CollapsibleSettingCardGroup(self.tr("哔哩哔哩视频下载"), "bili", settingPage.container)
        self.biliGroup.addSettingCards([
            ComboBoxSettingCard(
                self.defaultQuality, FluentIcon.VIDEO, self.tr("默认清晰度"),
                self.tr("下载视频时默认的清晰度"),
                ["8K", "4K", "1080P60", "1080P+", "1080P", "720P60", "720P", "480P", "360P"],
                self.biliGroup,
            ),
            ComboBoxSettingCard(
                self.alternativeQuality, FluentIcon.VIDEO, self.tr("备选清晰度"),
                self.tr("下载视频时备选的清晰度"),
                [self.tr("可以下载的最高画质"), self.tr("可以下载的最低画质")],
                self.biliGroup,
            ),
            SwitchSettingCard(FluentIcon.VIDEO, self.tr("HDR"),
                self.tr("下载 HDR 视频"), self.shouldIncludeHdr, self.biliGroup),
            SwitchSettingCard(FluentIcon.VIDEO, self.tr("杜比视界"),
                self.tr("下载杜比视界视频"), self.shouldIncludeDolby, self.biliGroup),
            BilibiliLoginSettingCard(self.biliGroup),
        ])
        settingPage.addSettingGroup(self.biliGroup)
bilibiliConfig = BilibiliConfig()

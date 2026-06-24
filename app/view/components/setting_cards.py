from __future__ import annotations

from urllib.parse import urlsplit

from PySide6.QtCore import Qt, QEvent, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QButtonGroup, QHBoxLayout,
    QSpacerItem, QSizePolicy, QFileDialog,
)
from qfluentwidgets import (
    SettingCard, PushSettingCard, RangeConfigItem, SpinBox,
    ExpandGroupSettingCard, ConfigItem, FluentIcon, BodyLabel,
    RadioButton, ComboBox, LineEdit, ToolButton, ToolTipFilter,
)

from app.config.cfg import cfg, proxies


class SpinBoxSettingCard(SettingCard):

    def __init__(self, configItem: RangeConfigItem, icon, title: str,
                 content: str = "", parent=None, suffix: str = "",
                 singleStep: int = 50, division: float = 1):
        super().__init__(icon, title, content, parent)
        self._configItem = configItem
        self._division = division

        self.spinBox = SpinBox(self)
        self.spinBox.setSingleStep(singleStep)
        self.spinBox.setMinimumWidth(180)
        self.spinBox.setSuffix(suffix)
        self.spinBox.installEventFilter(self)
        r = configItem.range
        self.spinBox.setRange(int(r[0] * division), int(r[1] * division))
        self.spinBox.setValue(int(configItem.value * division))

        self.hBoxLayout.addWidget(self.spinBox)
        self.hBoxLayout.addSpacing(24)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Wheel:
            return True
        return super().eventFilter(watched, event)

    def leaveEvent(self, event):
        cfg.set(self._configItem, self.spinBox.value() / self._division)


class LineEditSettingCard(SettingCard):

    def __init__(self, configItem: ConfigItem, icon, title: str,
                 content: str = "", parent=None, placeholder: str = ""):
        super().__init__(icon, title, content, parent)
        self._configItem = configItem

        self.lineEdit = LineEdit(self)
        self.lineEdit.setMinimumWidth(180)
        self.lineEdit.setClearButtonEnabled(True)
        self.lineEdit.setPlaceholderText(placeholder)
        if configItem:
            self.lineEdit.setText(configItem.value)

        self.hBoxLayout.addWidget(self.lineEdit)
        self.hBoxLayout.addSpacing(16)

        self.lineEdit.editingFinished.connect(
            lambda: cfg.set(self._configItem, self.lineEdit.text())
        )


class ProxySettingCard(ExpandGroupSettingCard):

    def __init__(self, configItem: ConfigItem, parent=None):
        super().__init__(FluentIcon.GLOBE, self.tr("代理"),
                         self.tr("设置下载时希望使用的代理"), parent=parent)
        self._configItem = configItem

        self.choiceLabel = BodyLabel(self)
        self.radioWidget = QWidget(self.view)
        self.radioLayout = QVBoxLayout(self.radioWidget)

        self.buttonGroup = QButtonGroup(self)
        self.offRadio = RadioButton(self.tr("不使用代理"), self.radioWidget)
        self.autoRadio = RadioButton(self.tr("自动检测系统代理"), self.radioWidget)
        self.customRadio = RadioButton(self.tr("使用自定义代理"), self.radioWidget)

        self.customWidget = QWidget(self.view)
        self.customLayout = QHBoxLayout(self.customWidget)
        self.protocolCombo = ComboBox(self.customWidget)
        self.protocolCombo.addItems(["socks4", "socks5", "http", "https"])
        self.ipEdit = LineEdit(self.customWidget)
        self.ipEdit.setPlaceholderText(self.tr("代理 IP 地址"))
        self.portEdit = LineEdit(self.customWidget)
        self.portEdit.setPlaceholderText(self.tr("端口"))

        self.credWidget = QWidget(self.view)
        self.credLayout = QHBoxLayout(self.credWidget)
        self.userEdit = LineEdit(self.credWidget)
        self.userEdit.setPlaceholderText(self.tr("用户名（可选）"))
        self.passEdit = LineEdit(self.credWidget)
        self.passEdit.setPlaceholderText(self.tr("密码（可选）"))
        self.passEdit.setEchoMode(LineEdit.EchoMode.Password)

        self._initLayout()

        value = configItem.value
        if value == "Auto":
            self.autoRadio.setChecked(True)
            self._onRadioClicked(self.autoRadio)
        elif value == "Off":
            self.offRadio.setChecked(True)
            self._onRadioClicked(self.offRadio)
        else:
            self.customRadio.setChecked(True)
            self._onRadioClicked(self.customRadio)
            self._showProxyUrl(value)

        self.buttonGroup.buttonClicked.connect(self._onRadioClicked)

    def _initLayout(self) -> None:
        self.addWidget(self.choiceLabel)

        self.radioLayout.setSpacing(19)
        self.radioLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.radioLayout.setContentsMargins(48, 5, 0, 18)
        for btn in (self.offRadio, self.autoRadio, self.customRadio):
            self.buttonGroup.addButton(btn)
            self.radioLayout.addWidget(btn)

        self.customLayout.setContentsMargins(48, 5, 44, 10)
        self.customLayout.addWidget(BodyLabel(self.tr("编辑代理服务器: "), self.customWidget))
        self.customLayout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.customLayout.addWidget(self.protocolCombo)
        self.customLayout.addWidget(BodyLabel("://", self.customWidget))
        self.customLayout.addWidget(self.ipEdit)
        self.customLayout.addWidget(BodyLabel(":", self.customWidget))
        self.customLayout.addWidget(self.portEdit)

        self.credLayout.setContentsMargins(48, 5, 44, 18)
        self.credLayout.addWidget(BodyLabel(self.tr("认证信息: "), self.credWidget))
        self.credLayout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.credLayout.addWidget(self.userEdit)
        self.credLayout.addWidget(BodyLabel(" : ", self.credWidget))
        self.credLayout.addWidget(self.passEdit)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.radioWidget)
        self.addGroupWidget(self.customWidget)
        self.addGroupWidget(self.credWidget)

    def _onRadioClicked(self, button) -> None:
        self.choiceLabel.setText(button.text())
        self.choiceLabel.adjustSize()
        isCustom = button is self.customRadio
        self.customWidget.setEnabled(isCustom)
        self.credWidget.setEnabled(isCustom)

        if button is self.autoRadio:
            cfg.set(self._configItem, "Auto")
            detected = proxies()
            url = next((detected.get(p) for p in ("https", "http", "ftp") if detected and detected.get(p)), None) if detected else None
            self._showProxyUrl(url)
        elif button is self.offRadio:
            cfg.set(self._configItem, "Off")

    def _showProxyUrl(self, proxyUrl: str | None) -> None:
        if not proxyUrl:
            self.protocolCombo.setCurrentText("")
            self.ipEdit.setText(self.tr("未检测到代理"))
            self.portEdit.setText("")
            self.userEdit.setText("")
            self.passEdit.setText("")
            return
        parsed = urlsplit(proxyUrl)
        self.protocolCombo.setCurrentText(parsed.scheme)
        self.ipEdit.setText(parsed.hostname or "")
        self.portEdit.setText(str(parsed.port or ""))
        self.userEdit.setText(parsed.username or "")
        self.passEdit.setText(parsed.password or "")

    def _buildProxyUrl(self) -> str:
        protocol = self.protocolCombo.currentText()
        ip = self.ipEdit.text()
        port = self.portEdit.text()
        user = self.userEdit.text()
        password = self.passEdit.text()
        cred = f"{user}:{password}@" if user or password else ""
        return f"{protocol}://{cred}{ip}:{port}"

    def leaveEvent(self, event):
        if self.customRadio.isChecked():
            url = self._buildProxyUrl()
            if cfg.proxyServer.validator.validate(url):
                cfg.set(self._configItem, url)
            else:
                self.autoRadio.click()


class SelectFolderSettingCard(SettingCard):
    pathChanged = Signal(str)

    def __init__(self, configItem: ConfigItem, defaultPath: str,
                 title: str, browseTitle: str, parent=None):
        super().__init__(FluentIcon.FOLDER, title, configItem.value, parent)
        self._configItem = configItem
        self._defaultPath = defaultPath
        self._browseTitle = browseTitle

        self.chooseFolderButton = ToolButton(FluentIcon.FOLDER, self)
        self.restoreButton = ToolButton(FluentIcon.CANCEL, self)
        self.chooseFolderButton.setToolTip(self.tr("浏览文件夹"))
        self.chooseFolderButton.installEventFilter(ToolTipFilter(self.chooseFolderButton))
        self.restoreButton.setToolTip(self.tr("恢复默认路径"))
        self.restoreButton.installEventFilter(ToolTipFilter(self.restoreButton))

        self.hBoxLayout.addWidget(self.chooseFolderButton, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(8)
        self.hBoxLayout.addWidget(self.restoreButton, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self.chooseFolderButton.clicked.connect(self._onChooseFolder)
        self.restoreButton.clicked.connect(lambda: self._setPath(self._defaultPath))

    def _onChooseFolder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self.window(), self._browseTitle)
        if folder:
            self._setPath(folder)

    def _setPath(self, path: str) -> None:
        cfg.set(self._configItem, path)
        self.setContent(self._configItem.value)
        self.pathChanged.emit(self._configItem.value)


class ClientProfileSettingCard(SettingCard):
    FAMILY_LABELS = {"chrome": "Chrome", "edge": "Edge", "firefox": "Firefox", "safari": "Safari", "okhttp": "OkHttp"}

    def __init__(self, parent=None):
        from qfluentwidgets import DropDownPushButton
        super().__init__(FluentIcon.ROBOT, self.tr("模拟身份"), self.tr("浏览器 TLS 指纹与 User-Agent"), parent)
        self.button = DropDownPushButton(self._label(cfg.clientProfile.value), self)
        self._initWidget()
        self._initLayout()
        self._bind()

    def _initWidget(self) -> None:
        from qfluentwidgets import Action, RoundMenu
        from app.client import profileFamilies, profileVersions

        self.button.setMinimumWidth(200)
        menu = RoundMenu(parent=self)

        for value, icon in (("auto", FluentIcon.ROBOT), ("raw", FluentIcon.CANCEL)):
            action = Action(icon, self._label(value), self)
            action.triggered.connect(lambda checked=False, v=value: self._onPick(v))
            menu.addAction(action)

        for family in profileFamilies():
            submenu = RoundMenu(self.FAMILY_LABELS.get(family, family), self)
            latest = Action(self._label(family), self)
            latest.triggered.connect(lambda checked=False, v=family: self._onPick(v))
            submenu.addAction(latest)
            submenu.addSeparator()
            for name in profileVersions(family):
                action = Action(self._label(name), self)
                action.triggered.connect(lambda checked=False, v=name: self._onPick(v))
                submenu.addAction(action)
            menu.addMenu(submenu)

        self.button.setMenu(menu)

    def _initLayout(self) -> None:
        self.hBoxLayout.addWidget(self.button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

    def _bind(self) -> None:
        cfg.clientProfile.valueChanged.connect(lambda v: self.button.setText(self._label(v)))

    def _onPick(self, value: str) -> None:
        cfg.set(cfg.clientProfile, value)

    def _label(self, value: str) -> str:
        if value in {"", "auto"}:
            return self.tr("自动（匹配来源）")
        if value == "raw":
            return self.tr("不模拟（原样发送）")
        if value in self.FAMILY_LABELS:
            return f"{self.FAMILY_LABELS[value]}（最新）"
        head = value.rstrip("0123456789_")
        version = value[len(head):].replace("_", ".")
        return f"{head} {version}" if version else value


class DefaultHeadersSettingCard(PushSettingCard):
    def __init__(self, icon, title: str, content: str = "", parent=None):
        super().__init__(self.tr("编辑"), icon, title, content, parent)
        self.clicked.connect(self._onClicked)

    def _onClicked(self) -> None:
        from qfluentwidgets import MessageBoxBase, SubtitleLabel
        from app.view.components.editors import AutoSizingEdit, headersToText, headersFromText

        dialog = MessageBoxBase(self.window())
        dialog.widget.setMinimumWidth(500)
        dialog.viewLayout.addWidget(SubtitleLabel(self.tr("编辑默认请求头"), dialog))
        edit = AutoSizingEdit(dialog, minimumVisibleLines=8, maximumVisibleLines=20)
        edit.setPlainText(headersToText(cfg.defaultRequestHeaders.value))
        dialog.viewLayout.addWidget(edit)

        if dialog.exec():
            headers = headersFromText(edit.toPlainText())
            if headers:
                cfg.set(cfg.defaultRequestHeaders, headers)

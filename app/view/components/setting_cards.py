from __future__ import annotations

from urllib.parse import urlsplit

from PySide6.QtCore import Qt, QEvent, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QButtonGroup, QHBoxLayout,
    QSpacerItem, QSizePolicy, QFileDialog,
)
from qfluentwidgets import (
    SettingCard, PushSettingCard, RangeConfigItem, SpinBox,
    ExpandGroupSettingCard, ConfigItem, FluentIcon, BodyLabel, CaptionLabel,
    RadioButton, ComboBox, LineEdit, ToolButton, ToolTipFilter,
    PrimaryPushButton, InfoBar, InfoBarPosition,
    IconWidget,
)

from app.config.cfg import cfg, proxyUrl
from app.view.components.banners import WarningBanner


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

        self.compatBanner = WarningBanner(self.view)
        self.compatBanner.setContentsMargins(48, 0, 44, 10)
        bannerLayout = QHBoxLayout(self.compatBanner)
        bannerLayout.setContentsMargins(10, 8, 10, 8)
        bannerLayout.setSpacing(8)
        bannerIcon = IconWidget(FluentIcon.INFO, self.compatBanner)
        bannerIcon.setFixedSize(16, 16)
        bannerLayout.addWidget(bannerIcon)
        bannerLayout.addWidget(CaptionLabel(
            self.tr("当前代理类型可能不适用于所有下载方式，SOCKS5 可兼容全部"), self.compatBanner,
        ), 1)

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
        self.protocolCombo.currentTextChanged.connect(self._refreshCompatBanner)
        self._refreshCompatBanner()

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
        self.addGroupWidget(self.compatBanner)

    def _onRadioClicked(self, button) -> None:
        self.choiceLabel.setText(button.text())
        self.choiceLabel.adjustSize()
        isCustom = button is self.customRadio
        self.customWidget.setEnabled(isCustom)
        self.credWidget.setEnabled(isCustom)

        if button is self.autoRadio:
            cfg.set(self._configItem, "Auto")
            self._showProxyUrl(proxyUrl())
        elif button is self.offRadio:
            cfg.set(self._configItem, "Off")
        self._refreshCompatBanner()

    def _showProxyUrl(self, url: str | None) -> None:
        if not url:
            self.protocolCombo.setCurrentText("")
            self.ipEdit.setText(self.tr("未检测到代理"))
            self.portEdit.setText("")
            self.userEdit.setText("")
            self.passEdit.setText("")
            return
        parsed = urlsplit(url)
        self.protocolCombo.setCurrentText(parsed.scheme)
        self.ipEdit.setText(parsed.hostname or "")
        self.portEdit.setText(str(parsed.port or ""))
        self.userEdit.setText(parsed.username or "")
        self.passEdit.setText(parsed.password or "")

    def _refreshCompatBanner(self) -> None:
        if self.offRadio.isChecked():
            self.compatBanner.setVisible(False)
            return
        if self.autoRadio.isChecked():
            url = proxyUrl()
            scheme = urlsplit(url).scheme.lower() if url else ""
        else:
            scheme = self.protocolCombo.currentText().lower()
        if not scheme:
            self.compatBanner.setVisible(False)
            return
        from app.services.feature_service import featureService
        self.compatBanner.setVisible(any(
            p.proxySchemes is not None and scheme not in p.proxySchemes
            for p in featureService.packs
        ))

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
                 title: str, parent=None):
        super().__init__(FluentIcon.FOLDER, title, "", parent)
        self._configItem = configItem
        self._defaultPath = defaultPath

        from app.view.components.editors import FolderPicker

        self.picker = FolderPicker(self)
        self.restoreButton = ToolButton(FluentIcon.CANCEL, self)
        self.restoreButton.setToolTip(self.tr("恢复默认路径"))
        self.restoreButton.installEventFilter(ToolTipFilter(self.restoreButton))

        self.picker.refreshHistory()
        self.picker.setPath(configItem.value)

        self.hBoxLayout.addWidget(self.picker, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(8)
        self.hBoxLayout.addWidget(self.restoreButton, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self.picker.pathChanged.connect(self._onPathChanged)
        self.restoreButton.clicked.connect(self._onResetClicked)

    def _onPathChanged(self, path: str) -> None:
        cfg.set(self._configItem, path)
        self._addToHistory(path)
        self.picker.refreshHistory()
        self.pathChanged.emit(path)

    def _onResetClicked(self) -> None:
        self.picker.setPath(self._defaultPath)
        cfg.set(self._configItem, self._defaultPath)

    def _addToHistory(self, folder: str) -> None:
        history = list(cfg.memoryDownloadFolders.value)
        if folder in history:
            history.remove(folder)
        history.insert(0, folder)
        cfg.set(cfg.memoryDownloadFolders, history[:20])


class ClientProfileSettingCard(SettingCard):

    def __init__(self, parent=None):
        from qfluentwidgets import DropDownPushButton
        from app.client import toProfileLabel
        super().__init__(FluentIcon.ROBOT, self.tr("模拟身份"), self.tr("浏览器 TLS 指纹与 User-Agent"), parent)
        self.button = DropDownPushButton(toProfileLabel(cfg.clientProfile.value), self)
        self._initWidget()
        self._initLayout()
        self._bind()

    def _initWidget(self) -> None:
        from qfluentwidgets import Action, RoundMenu
        from app.client import (
            PROFILE_FAMILY_LABELS, profileFamilies, profileVersions, toProfileLabel,
        )

        self.button.setMinimumWidth(200)
        menu = RoundMenu(parent=self)

        for value, icon in (("auto", FluentIcon.ROBOT), ("raw", FluentIcon.CANCEL)):
            action = Action(icon, toProfileLabel(value), self)
            action.triggered.connect(lambda checked=False, v=value: self._onPick(v))
            menu.addAction(action)

        for family in profileFamilies():
            submenu = RoundMenu(PROFILE_FAMILY_LABELS.get(family, family), self)
            latest = Action(toProfileLabel(family), self)
            latest.triggered.connect(lambda checked=False, v=family: self._onPick(v))
            submenu.addAction(latest)
            submenu.addSeparator()
            for name in profileVersions(family):
                action = Action(toProfileLabel(name), self)
                action.triggered.connect(lambda checked=False, v=name: self._onPick(v))
                submenu.addAction(action)
            menu.addMenu(submenu)

        self.button.setMenu(menu)

    def _initLayout(self) -> None:
        self.hBoxLayout.addWidget(self.button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

    def _bind(self) -> None:
        from app.client import toProfileLabel
        cfg.clientProfile.valueChanged.connect(lambda v: self.button.setText(toProfileLabel(v)))

    def _onPick(self, value: str) -> None:
        cfg.set(cfg.clientProfile, value)


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


class SelectFileCard(SettingCard):
    pathChanged = Signal(str)

    def __init__(self, configItem: ConfigItem, icon, title: str, hint: str,
                 browseTitle: str, parent=None):
        super().__init__(icon, title, configItem.value or hint, parent)
        self._configItem = configItem
        self._hint = hint
        self._browseTitle = browseTitle

        self.chooseFileButton = ToolButton(FluentIcon.FOLDER, self)
        self.clearButton = ToolButton(FluentIcon.CANCEL, self)
        self.chooseFileButton.setToolTip(self.tr("选择文件"))
        self.chooseFileButton.installEventFilter(ToolTipFilter(self.chooseFileButton))
        self.clearButton.setToolTip(self.tr("清除路径"))
        self.clearButton.installEventFilter(ToolTipFilter(self.clearButton))

        self.hBoxLayout.addWidget(self.chooseFileButton, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(8)
        self.hBoxLayout.addWidget(self.clearButton, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self.chooseFileButton.clicked.connect(self._onChooseFile)
        self.clearButton.clicked.connect(lambda: self._setPath(""))

    def _onChooseFile(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self.window(), self._browseTitle)
        if path:
            self._setPath(path)

    def _setPath(self, path: str) -> None:
        cfg.set(self._configItem, path)
        self.setContent(path or self._hint)
        self.pathChanged.emit(path)


class RuntimeCard(SettingCard):

    def __init__(self, runtime, parent=None):
        from app.models.pack import BinaryRuntime
        self._runtime: BinaryRuntime = runtime
        super().__init__(FluentIcon.INFO, runtime.name, self.tr("正在检测运行时..."), parent)

        self.installButton = PrimaryPushButton(self.tr("一键安装"), self)
        self.refreshButton = ToolButton(FluentIcon.SYNC, self)

        self._initWidget()
        self._initLayout()
        self._bind()

    def _initWidget(self) -> None:
        self.refreshButton.setToolTip(self.tr("刷新"))
        self.refreshButton.installEventFilter(ToolTipFilter(self.refreshButton))

    def _initLayout(self) -> None:
        self.hBoxLayout.addWidget(self.installButton, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(8)
        self.hBoxLayout.addWidget(self.refreshButton, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

    def _bind(self) -> None:
        self.installButton.clicked.connect(self._onInstallClicked)
        self.refreshButton.clicked.connect(self.refreshStatus)

    def refreshStatus(self) -> None:
        from app.services.coroutine_runner import coroutineRunner

        self.refreshButton.setEnabled(False)
        self.setContent(self.tr("正在检测运行时..."))
        coroutineRunner.submit(
            self._runtime.probeVersion(),
            done=self._onProbeFinished,
            failed=self._onProbeFailed,
        )

    def _onProbeFinished(self, version: str) -> None:
        self.refreshButton.setEnabled(True)
        path = self._runtime.path()
        if version and path:
            self.setContent(self.tr("版本: {0}\n路径: {1}").format(version, path))
        elif path:
            self.setContent(self.tr("路径: {0}").format(path))
        else:
            self.setContent(self.tr("未检测到可用的 {0}").format(self._runtime.name))

    def _onProbeFailed(self, error: str) -> None:
        self.refreshButton.setEnabled(True)
        self.setContent(self.tr("检测运行时失败"))

    def _onInstallClicked(self) -> None:
        from app.services.coroutine_runner import coroutineRunner

        self.installButton.setEnabled(False)
        self.installButton.setText(self.tr("准备中..."))
        coroutineRunner.submit(
            self._runtime.installTask(),
            done=self._onInstallTaskCreated,
            failed=self._onInstallTaskFailed,
        )

    def _onInstallTaskCreated(self, task) -> None:
        from app.services.task_service import taskService

        self.installButton.setEnabled(True)
        self.installButton.setText(self.tr("一键安装"))
        taskService.add(task)

    def _onInstallTaskFailed(self, error: str) -> None:
        self.installButton.setEnabled(True)
        self.installButton.setText(self.tr("一键安装"))
        InfoBar.error(
            self.tr("安装失败"),
            error,
            duration=-1,
            position=InfoBarPosition.TOP,
            parent=self.window(),
        )

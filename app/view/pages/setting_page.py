from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget, QApplication
from qfluentwidgets import (
    ComboBoxSettingCard, FluentIcon, HyperlinkCard, InfoBar,
    InfoBarPosition, PrimaryPushSettingCard,
    RangeSettingCard, ScrollArea, SwitchSettingCard,
)

from app.config.cfg import cfg
from app.config.constants import (
    AUTHOR, AUTHOR_URL, EDGE_ADDONS_URL, FEEDBACK_URL,
    FIREFOX_ADDONS_URL, VERSION, YEAR,
)
from app.view.components.setting_card_group import CollapsibleSettingCardGroup
from app.view.components.setting_cards import ProxySettingCard, SpinBoxSettingCard


class SettingPage(ScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.container = QWidget()
        self.vBoxLayout = QVBoxLayout(self.container)
        self.vBoxLayout.addStretch(1)

        self.generalGroup = CollapsibleSettingCardGroup(self.tr("综合下载设置"), "general", self.container)
        self.categoryGroup = CollapsibleSettingCardGroup(self.tr("下载分类"), "category", self.container)
        self.browserGroup = CollapsibleSettingCardGroup(self.tr("浏览器扩展"), "browser", self.container)
        self.personalGroup = CollapsibleSettingCardGroup(self.tr("个性化"), "personalization", self.container)
        self.softwareGroup = CollapsibleSettingCardGroup(self.tr("应用"), "software", self.container)
        self.aboutGroup = CollapsibleSettingCardGroup(self.tr("关于"), "about", self.container)

        self._initWidget()
        self._initCards()
        self._initLayout()
        self._bind()

    def addSettingGroup(self, group: CollapsibleSettingCardGroup) -> None:
        self.vBoxLayout.insertWidget(self.vBoxLayout.count() - 1, group)

    def _initWidget(self) -> None:
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setObjectName("SettingPage")
        self.enableTransparentBackground()

    def _initCards(self) -> None:
        self.generalGroup.addSettingCards([
            RangeSettingCard(cfg.maxTaskNum, FluentIcon.TRAIN, self.tr("最大任务数"),
                             self.tr("最多能同时进行的任务数量")),
            RangeSettingCard(cfg.preBlockNum, FluentIcon.CLOUD, self.tr("预分配线程数"),
                             self.tr("线程越多，下载越快。线程数大于 64 时，有触发反爬导致文件损坏的风险")),
            SwitchSettingCard(FluentIcon.SPEED_HIGH, self.tr("自动提速"),
                              self.tr("AI 实时检测各线程效率并自动增加线程数以提高下载速度"),
                              cfg.autoSpeedUp),
            RangeSettingCard(cfg.maxReassignSize, FluentIcon.LIBRARY, self.tr("最大重新分配大小 (MB)"),
                             self.tr("每线程剩余量大于此值时, 有线程完成或自动提速条件满足会触发重新分配")),
            SwitchSettingCard(FluentIcon.DEVELOPER_TOOLS, self.tr("下载时验证 SSL 证书"),
                              self.tr("文件无法下载时，可尝试关闭该选项"),
                              cfg.shouldVerifySsl),
            ProxySettingCard(cfg.proxyServer),
        ])

        self.categoryGroup.addSettingCards([
            SwitchSettingCard(FluentIcon.TAG, self.tr("启用下载分类"),
                              self.tr("根据扩展名将下载任务归类，便于筛选与分发到指定文件夹"),
                              cfg.isCategoryEnabled),
        ])

        self.browserGroup.addSettingCards([
            SwitchSettingCard(FluentIcon.CONNECT, self.tr("启用浏览器扩展"),
                              self.tr("接收来自浏览器的下载信息，请安装浏览器扩展后使用"),
                              cfg.isBrowserExtensionEnabled),
            SwitchSettingCard(FluentIcon.CHAT, self.tr("收到下载信息时弹出窗口"),
                              self.tr("收到下载信息时弹出窗口，方便您调整下载参数"),
                              cfg.shouldRaiseWindowOnBrowserTask),
        ])

        self.personalGroup.addSettingCards([
            ComboBoxSettingCard(cfg.customThemeMode, FluentIcon.BRUSH, self.tr("应用主题"),
                                self.tr("更改应用程序的外观"),
                                texts=[self.tr("浅色"), self.tr("深色"), self.tr("跟随系统设置")]),
            ComboBoxSettingCard(cfg.language, FluentIcon.LANGUAGE, self.tr("语言"),
                                self.tr("设置界面的首选语言"),
                                texts=["简体中文 (中国大陆)", "正體中文 (台灣)", "粤语 (香港)",
                                       "English (US)", "日本語 (日本)", "Русский (Россия)",
                                       self.tr("使用系统设置")]),
        ])
        if sys.platform == "win32":
            self.personalGroup.addSettingCard(
                ComboBoxSettingCard(cfg.backgroundEffect, FluentIcon.TRANSPARENT,
                                    self.tr("窗口背景透明材质"),
                                    self.tr("设置窗口背景透明效果和透明材质"),
                                    texts=["Acrylic", "Mica", "MicaAlt", "Aero", "None"]),
            )
        if sys.platform == "darwin":
            self.personalGroup.addSettingCards([
                SwitchSettingCard(FluentIcon.APPLICATION, self.tr("在 Dock 栏中显示程序"),
                                  self.tr("关闭后可通过菜单栏图标继续使用程序"),
                                  cfg.shouldShowDockIcon),
                SwitchSettingCard(FluentIcon.SPEED_HIGH, self.tr("在 Dock 图标上显示实时速度"),
                                  self.tr("下载时在程序坞图标上叠加当前速度"),
                                  cfg.shouldShowDockSpeed),
                SwitchSettingCard(FluentIcon.SPEED_HIGH, self.tr("在菜单栏显示实时速度"),
                                  self.tr("下载时在菜单栏图标旁显示当前速度"),
                                  cfg.shouldShowMenuBarSpeed),
            ])

        self.softwareGroup.addSettingCards([
            SwitchSettingCard(FluentIcon.UPDATE, self.tr("在应用程序启动时检查更新"),
                              self.tr("新版本将更稳定，并具有更多功能"),
                              cfg.shouldCheckUpdateAtStartup),
            SwitchSettingCard(FluentIcon.VPN, self.tr("开机启动"),
                              self.tr("在系统启动时静默运行 Ghost Downloader"),
                              cfg.shouldRunAtLogin),
            SwitchSettingCard(FluentIcon.PASTE, self.tr("剪贴板监听"),
                              self.tr("剪贴板监听器将自动检测剪贴板中的链接并添加下载任务"),
                              cfg.isClipboardListenerEnabled),
        ])

        self.aboutGroup.addSettingCards([
            HyperlinkCard(AUTHOR_URL, self.tr("打开作者的个人空间"), FluentIcon.PROJECTOR,
                          self.tr("了解作者"), self.tr("发现更多 {} 的作品").format(AUTHOR)),
            PrimaryPushSettingCard(self.tr("提供反馈"), FluentIcon.FEEDBACK,
                                   self.tr("提供反馈"),
                                   self.tr("通过提供反馈来帮助我们改进 Ghost Downloader")),
            PrimaryPushSettingCard(self.tr("检查更新"), FluentIcon.INFO, self.tr("关于"),
                                   f"© Copyright {YEAR}, {AUTHOR}. Version {VERSION}"),
        ])

    def _initLayout(self) -> None:
        self.addSettingGroup(self.generalGroup)
        self.addSettingGroup(self.categoryGroup)
        self.addSettingGroup(self.browserGroup)
        self.addSettingGroup(self.personalGroup)
        self.addSettingGroup(self.softwareGroup)
        self.addSettingGroup(self.aboutGroup)

    def _bind(self) -> None:
        cfg.appRestartSig.connect(self._showRestartTooltip)

    def _onRunAtLoginChanged(self, enabled: bool) -> None:
        from app.platform.run_at_login import setRunAtLogin
        setRunAtLogin(enabled)

    def _onExportBrowserExtensionClicked(self) -> None:
        from PySide6.QtCore import QResource
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, self.tr("选择导出路径"), "./Extension.crx", "Chromium Extension(*.crx)")
        if path:
            with open(path, "wb") as f:
                f.write(QResource(":/res/chrome_extension.crx").data())

    def _onRegenerateTokenClicked(self) -> None:
        from app.services.browser_service import browserService
        token = browserService.regenerateToken()
        QApplication.clipboard().setText(token)
        InfoBar.success(self.tr("已重新生成配对令牌"), self.tr("新令牌已复制到剪贴板"),
                        duration=2000, position=InfoBarPosition.BOTTOM_RIGHT, parent=self.window())

    def _onAboutCardClicked(self) -> None:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        from app.config.constants import FEEDBACK_URL
        QDesktopServices.openUrl(QUrl(FEEDBACK_URL))

    def _showRestartTooltip(self) -> None:
        InfoBar.success(self.tr("已配置"), self.tr("重启软件后生效"), duration=1500, parent=self)

    def showEvent(self, event) -> None:
        self._restoreOrder()
        super().showEvent(event)

    def _restoreOrder(self) -> None:
        groups = [
            self.vBoxLayout.itemAt(i).widget()
            for i in range(self.vBoxLayout.count())
            if self.vBoxLayout.itemAt(i).widget()
        ]
        keyToWidget = {g.objectName(): g for g in groups}
        order = [k for k in cfg.settingGroupOrder.value if k in keyToWidget]
        rest = [k for k in keyToWidget if k not in order]
        aboutKey = self.aboutGroup.objectName()
        if aboutKey in rest:
            rest.remove(aboutKey)
            rest.append(aboutKey)
        order += rest
        for idx, key in enumerate(order):
            self.vBoxLayout.insertWidget(idx, keyToWidget[key])
        for g in groups:
            if isinstance(g, CollapsibleSettingCardGroup):
                g.updateArrows()

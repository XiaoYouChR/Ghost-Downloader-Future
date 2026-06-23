from urllib.parse import urlparse

from app.client import buildClient
from app.config.cfg import ConfigItem
from app.models.pack import PackConfig
from qfluentwidgets import BoolValidator, ComboBox, ConfigValidator, FluentIcon, LineEdit, SettingCard, ToolButton, ToolTipFilter

GITHUB_PROXY_SITES = (
    "https://gh-proxy.com/",
    "https://ghproxy.vip/",
    "https://ghproxy.homeboyc.cn/",
    "https://gh.llkk.cc/",
)
CUSTOM_SITE_KEY = "__custom__"
PROBE_TARGET = "https://raw.githubusercontent.com/asjdf/ghproxy/main/src/index.ts"


def toProxySite(site: str) -> str:
    value = str(site or "").strip()
    if not value:
        return ""
    if "://" not in value:
        value = f"https://{value}"
    return value.rstrip("/")


def selectedProxySite() -> str:
    if githubConfig.selectedSite.value == CUSTOM_SITE_KEY:
        return githubConfig.customSite.value
    return githubConfig.selectedSite.value


async def probeProxyLatencies() -> dict[str, int]:
    import asyncio
    from time import perf_counter

    sites = list(GITHUB_PROXY_SITES)
    custom = githubConfig.customSite.value
    if custom:
        sites.append(custom)

    async def probeOne(site: str) -> tuple[str, int]:
        url = f"{site.rstrip('/')}/{PROBE_TARGET}"
        client = buildClient()
        try:
            start = perf_counter()
            response = await asyncio.wait_for(client.get(url), timeout=10)
            elapsed = int((perf_counter() - start) * 1000)
            return site, elapsed if response.status_code < 400 else -1
        except Exception:
            return site, -1
        finally:
            await client.aclose()

    results = await asyncio.gather(*(probeOne(s) for s in sites))
    return dict(results)


class GitHubProxySiteValidator(ConfigValidator):
    def validate(self, value) -> bool:
        site = toProxySite(value)
        if not site:
            return False
        parsed = urlparse(site)
        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.netloc)
            and not parsed.params
            and not parsed.query
            and not parsed.fragment
        )

    def correct(self, value) -> str:
        site = toProxySite(value)
        return site if self.validate(site) else ""


class GitHubProxySiteCard(SettingCard):
    def __init__(self, parent=None):
        super().__init__(
            FluentIcon.GLOBE, self.tr("代理站"),
            self.tr("选择 GitHub 反向代理站，延迟仅供参考"), parent,
        )
        self._latencies: dict[str, int | None] = {s: None for s in GITHUB_PROXY_SITES}
        self._isRefreshing = False
        self.comboBox = ComboBox(self)
        self.customSiteEdit = LineEdit(self)
        self.refreshButton = ToolButton(FluentIcon.SYNC, self)

        self._initWidget()
        self._initLayout()
        self._bind()
        self._refreshItems()

    def _initWidget(self):
        self.comboBox.setMinimumWidth(260)
        self.customSiteEdit.setPlaceholderText("https://example.com/")
        self.customSiteEdit.setClearButtonEnabled(True)
        self.customSiteEdit.setMinimumWidth(220)
        self.refreshButton.setToolTip(self.tr("刷新延迟"))
        self.refreshButton.installEventFilter(ToolTipFilter(self.refreshButton))

    def _initLayout(self):
        self.hBoxLayout.addWidget(self.comboBox)
        self.hBoxLayout.addSpacing(8)
        self.hBoxLayout.addWidget(self.customSiteEdit)
        self.hBoxLayout.addSpacing(8)
        self.hBoxLayout.addWidget(self.refreshButton)
        self.hBoxLayout.addSpacing(16)

    def _bind(self):
        self.comboBox.currentIndexChanged.connect(self._onCurrentIndexChanged)
        self.customSiteEdit.editingFinished.connect(self._onCustomSiteEditingFinished)
        self.refreshButton.clicked.connect(self.refreshLatencies)

    def _refreshItems(self):
        from app.config.cfg import cfg
        currentSite = githubConfig.selectedSite.value
        if currentSite not in (*GITHUB_PROXY_SITES, CUSTOM_SITE_KEY):
            currentSite = GITHUB_PROXY_SITES[0]

        customSite = githubConfig.customSite.value
        self.comboBox.blockSignals(True)
        self.customSiteEdit.blockSignals(True)
        self.comboBox.clear()

        for site in GITHUB_PROXY_SITES:
            latency = self._latencies.get(site)
            displayName = urlparse(site).netloc or site.rstrip("/")
            label = displayName if latency is None else (
                f"{displayName} (超时)" if latency < 0 else f"{displayName} ({latency} ms)"
            )
            self.comboBox.addItem(label)

        customLabel = "自定义"
        if customSite:
            customLatency = self._latencies.get(customSite)
            if customLatency is not None:
                customLabel = f"自定义 ({customLatency} ms)" if customLatency >= 0 else "自定义 (超时)"
        self.comboBox.addItem(customLabel)

        if currentSite == CUSTOM_SITE_KEY:
            self.comboBox.setCurrentIndex(len(GITHUB_PROXY_SITES))
        elif currentSite in GITHUB_PROXY_SITES:
            self.comboBox.setCurrentIndex(GITHUB_PROXY_SITES.index(currentSite))
        else:
            self.comboBox.setCurrentIndex(0)

        self.customSiteEdit.setText(customSite)
        self.customSiteEdit.setVisible(currentSite == CUSTOM_SITE_KEY)
        self.comboBox.blockSignals(False)
        self.customSiteEdit.blockSignals(False)

    def _onCurrentIndexChanged(self, index: int):
        from app.config.cfg import cfg
        if index < 0:
            return
        if index < len(GITHUB_PROXY_SITES):
            cfg.set(githubConfig.selectedSite, GITHUB_PROXY_SITES[index])
        else:
            cfg.set(githubConfig.selectedSite, CUSTOM_SITE_KEY)
        self._refreshItems()

    def _onCustomSiteEditingFinished(self):
        from app.config.cfg import cfg
        cfg.set(githubConfig.customSite, self.customSiteEdit.text().strip())
        self._refreshItems()

    def refreshLatencies(self):
        if self._isRefreshing:
            return
        self._isRefreshing = True
        self._latencies = {s: None for s in GITHUB_PROXY_SITES}
        self._refreshItems()
        self.refreshButton.setEnabled(False)
        from app.services.coroutine_runner import coroutineRunner
        coroutineRunner.run(probeProxyLatencies(), self._onLatenciesDone, self._onLatenciesFailed)

    def _onLatenciesDone(self, latencies: dict[str, int]):
        self._isRefreshing = False
        self.refreshButton.setEnabled(True)
        self._latencies.update(latencies)
        self._refreshItems()

    def _onLatenciesFailed(self, error):
        self._isRefreshing = False
        self.refreshButton.setEnabled(True)


class GitHubConfig(PackConfig):
    enabled = ConfigItem("GitHub", "Enabled", True, BoolValidator())
    selectedSite = ConfigItem("GitHub", "SelectedSite", "", GitHubProxySiteValidator())
    customSite = ConfigItem("GitHub", "CustomSite", "", GitHubProxySiteValidator())

    def setupSettings(self, settingPage):
        from qfluentwidgets import FluentIcon, SwitchSettingCard
        from app.view.components.setting_card_group import CollapsibleSettingCardGroup

        self.githubGroup = CollapsibleSettingCardGroup(self.tr("GitHub 加速"), "github", settingPage.container)
        self.enableCard = SwitchSettingCard(
            FluentIcon.LINK, self.tr("启用 GitHub 加速"),
            self.tr("命中 GitHub 文件链接时，自动改写为所选反向代理站"),
            self.enabled, self.githubGroup,
        )
        self.proxySiteCard = GitHubProxySiteCard(self.githubGroup)

        self.githubGroup.addSettingCards([self.enableCard, self.proxySiteCard])
        settingPage.addSettingGroup(self.githubGroup)


githubConfig = GitHubConfig()

from qfluentwidgets import ConfigItem, FluentIconBase, SettingCard, PushSettingCard


class SpinBoxSettingCard(SettingCard):
    def __init__(self, configItem: ConfigItem, icon: FluentIconBase, title: str,
                 content: str = "", parent=None):
        super().__init__(icon, title, content, parent)


class LineEditSettingCard(SettingCard):
    def __init__(self, configItem: ConfigItem, icon: FluentIconBase, title: str,
                 content: str = "", parent=None):
        super().__init__(icon, title, content, parent)


class ProxySettingCard(SettingCard):
    def _initWidget(self) -> None:
        pass

    def _initLayout(self) -> None:
        pass

    def _bind(self) -> None:
        pass

    def _onRadioClicked(self, button) -> None:
        pass

    def _showProxyUrl(self, proxyUrl: str | None) -> None:
        pass

    def _buildProxyUrl(self) -> str:
        pass


class SelectFolderSettingCard(SettingCard):
    def __init__(self, configItem: ConfigItem, defaultPath: str,
                 title: str, browseTitle: str, parent=None):
        super().__init__(parent=parent)


class ClientProfileSettingCard(SettingCard):
    def _initWidget(self) -> None:
        pass

    def _initLayout(self) -> None:
        pass

    def _bind(self) -> None:
        pass


class DefaultHeadersSettingCard(PushSettingCard):
    def _bind(self) -> None:
        pass

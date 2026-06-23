from PySide6.QtWidgets import QWidget


class SettingPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def _initWidget(self) -> None:
        pass

    def _initLayout(self) -> None:
        pass

    def _bind(self) -> None:
        pass

    def _onRunAtLoginChanged(self, enabled: bool) -> None:
        pass

    def _onExportBrowserExtensionClicked(self) -> None:
        pass

    def _onRegenerateTokenClicked(self) -> None:
        pass

    def _onScanLoginClicked(self) -> None:
        pass

    def _onLogoutClicked(self) -> None:
        pass

    def _onAboutCardClicked(self) -> None:
        pass

    def _showRestartTooltip(self) -> None:
        pass

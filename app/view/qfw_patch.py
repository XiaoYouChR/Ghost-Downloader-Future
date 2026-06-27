"""qfluentwidgets 单例会按「窗口永生」假设持有 widget；窗口可死后需补偿。与库内部结构耦合。"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QStackedWidget


def patchFluentLabelThemeChanged() -> None:
    from qfluentwidgets.components.widgets import label as fluentLabelModule

    FluentLabelBase = fluentLabelModule.FluentLabelBase
    if getattr(FluentLabelBase, "_gdThemeChangedPatched", False):
        return

    def _init(self):
        fluentLabelModule.FluentStyleSheet.LABEL.apply(self)
        self.setFont(self.getFont())
        self.setTextColor()
        fluentLabelModule.qconfig.themeChanged.connect(self._applyThemeColor)
        self.customContextMenuRequested.connect(self._onContextMenuRequested)
        return self

    def _applyThemeColor(self, *_args) -> None:
        self.setTextColor(self.lightColor, self.darkColor)

    FluentLabelBase._init = _init
    FluentLabelBase._applyThemeColor = _applyThemeColor
    FluentLabelBase._gdThemeChangedPatched = True


def unregisterRouter(stacked: QStackedWidget) -> None:
    from qfluentwidgets.common.router import qrouter

    qrouter.history = [item for item in qrouter.history if item.stacked is not stacked]
    qrouter.stackHistories.pop(stacked, None)
    qrouter.emptyChanged.emit(not bool(qrouter.history))

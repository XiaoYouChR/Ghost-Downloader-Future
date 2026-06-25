from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QWidget
from qfluentwidgets import (
    Action, BodyLabel, FluentIcon, IconWidget, LineEdit, Slider,
)

from app.config.cfg import cfg


class SelectFolderCard(QWidget):

    def __init__(self, parent=None, *, initial: Path | None = None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self.iconWidget = IconWidget(FluentIcon.DOWNLOAD, self)
        self.iconWidget.setFixedSize(16, 16)
        self.titleLabel = BodyLabel(self.tr("选择下载路径"), self)
        self.pathEdit = LineEdit(self)
        self.pathEdit.setReadOnly(True)
        self.pathEdit.setText(str(initial) if initial else cfg.downloadFolder.value)
        browseAction = Action(FluentIcon.FOLDER, "", self)
        browseAction.triggered.connect(self._onBrowse)
        self.pathEdit.addAction(browseAction)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 5, 24, 5)
        layout.setSpacing(15)
        layout.addWidget(self.iconWidget)
        layout.addWidget(self.titleLabel)
        layout.addStretch(1)
        layout.addWidget(self.pathEdit, stretch=3)

    def options(self) -> dict:
        return {"outputFolder": Path(self.pathEdit.text())}

    def reset(self) -> None:
        self.pathEdit.setText(cfg.downloadFolder.value)

    def _onBrowse(self) -> None:
        path = Path(self.pathEdit.text())
        startDir = str(path if path.exists() else path.parent)
        selected = QFileDialog.getExistingDirectory(self, self.tr("选择下载路径"), startDir)
        if selected:
            self.pathEdit.setText(selected)


class SubworkerCountCard(QWidget):

    def __init__(self, parent=None, *, initial: int = 0):
        super().__init__(parent)
        self.setFixedHeight(50)
        self.iconWidget = IconWidget(FluentIcon.CLOUD, self)
        self.iconWidget.setFixedSize(16, 16)
        self.titleLabel = BodyLabel(self.tr("并行连接数"), self)
        self.slider = Slider(Qt.Orientation.Horizontal, self)
        self.valueLabel = BodyLabel(self)

        value = initial or cfg.preBlockNum.value
        self.slider.setMinimumWidth(268)
        self.slider.setSingleStep(1)
        self.slider.setRange(*cfg.preBlockNum.range)
        self.slider.setValue(value)
        self.valueLabel.setNum(value)
        self.slider.valueChanged.connect(self._onValueChanged)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 5, 24, 5)
        layout.setSpacing(15)
        layout.addWidget(self.iconWidget)
        layout.addWidget(self.titleLabel)
        layout.addStretch(1)
        layout.addWidget(self.valueLabel)
        layout.addSpacing(6)
        layout.addWidget(self.slider)
        layout.addSpacing(16)

    def options(self) -> dict:
        return {"subworkerCount": self.slider.value()}

    def reset(self) -> None:
        self.slider.setValue(cfg.preBlockNum.value)

    def _onValueChanged(self, value: int) -> None:
        self.valueLabel.setNum(value)
        self.valueLabel.adjustSize()


class ClientProfileCard(QWidget):

    def __init__(self, parent=None, *, initial: str = ""):
        from qfluentwidgets import DropDownPushButton, RoundMenu
        from app.client import (
            PROFILE_FAMILY_LABELS, profileFamilies, profileVersions, toProfileLabel,
        )

        super().__init__(parent)
        self.setFixedHeight(50)
        self._value = initial
        self.iconWidget = IconWidget(FluentIcon.ROBOT, self)
        self.iconWidget.setFixedSize(16, 16)
        self.titleLabel = BodyLabel(self.tr("模拟身份"), self)
        self.button = DropDownPushButton(toProfileLabel(initial), self)
        self.button.setMinimumWidth(200)

        menu = RoundMenu(parent=self)
        for value, icon in (("auto", FluentIcon.ROBOT), ("raw", FluentIcon.CANCEL)):
            action = Action(icon, toProfileLabel(value), self)
            action.triggered.connect(lambda _=False, v=value: self._onPick(v))
            menu.addAction(action)
        for family in profileFamilies():
            submenu = RoundMenu(PROFILE_FAMILY_LABELS.get(family, family), self)
            latest = Action(toProfileLabel(family), self)
            latest.triggered.connect(lambda _=False, v=family: self._onPick(v))
            submenu.addAction(latest)
            submenu.addSeparator()
            for name in profileVersions(family):
                action = Action(toProfileLabel(name), self)
                action.triggered.connect(lambda _=False, v=name: self._onPick(v))
                submenu.addAction(action)
            menu.addMenu(submenu)
        self.button.setMenu(menu)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 5, 24, 5)
        layout.setSpacing(15)
        layout.addWidget(self.iconWidget)
        layout.addWidget(self.titleLabel)
        layout.addStretch(1)
        layout.addWidget(self.button)

    def options(self) -> dict:
        return {"clientProfile": self._value}

    def reset(self) -> None:
        from app.client import toProfileLabel
        self._value = ""
        self.button.setText(toProfileLabel(""))

    def _onPick(self, value: str) -> None:
        from app.client import toProfileLabel
        self._value = value
        self.button.setText(toProfileLabel(value))

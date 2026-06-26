from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject

from app.config.paths import executableDir
from app.platform import file_association
from app.services.pack_loader import loadPacks

if TYPE_CHECKING:
    from app.models.pack import FeaturePack, TaskParser, FileType
    from app.models.task import Task, TaskOptions
    from PySide6.QtWidgets import QWidget


class FeatureService(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._packs: list[FeaturePack] = []
        self._parsers: list[TaskParser] = []
        self._packByPackId: dict[str, FeaturePack] = {}

    @property
    def packs(self) -> list[FeaturePack]:
        return self._packs

    def load(self) -> None:
        for pack in loadPacks(executableDir / "features"):
            self._register(pack)

    def start(self) -> None:
        for pack in self._packs:
            pack.start()

    def _register(self, pack: FeaturePack) -> None:
        self._packs.append(pack)
        self._packByPackId[pack.packId] = pack
        self._parsers.extend(pack.parsers())
        self._parsers.sort(key=lambda p: p.priority)
        if pack.config:
            toggle = pack.config.fileAssociationToggle()
            if toggle:
                toggle.connect(self._registerFileAssociations)

    async def parse(self, options: TaskOptions) -> Task:
        for parser in self._parsers:
            if parser.match(options):
                return await parser.parse(options)
        raise ValueError(f"No parser matched: {options.url}")

    def optionCards(self, task: Task, parent=None) -> list[QWidget]:
        pack = self._packByPackId.get(task.packId)
        return pack.optionCards(task, parent) if pack else []

    def taskCard(self, task: Task, parent=None):
        pack = self._packByPackId.get(task.packId)
        return pack.taskCard(task, parent) if pack else None

    def draftCard(self, task: Task, parent=None):
        pack = self._packByPackId.get(task.packId)
        return pack.draftCard(task, parent) if pack else None

    def pages(self) -> list:
        result = []
        for pack in self._packs:
            result.extend(pack.pages())
        return result

    def settingGroups(self, settingPage) -> None:
        for pack in self._packs:
            if pack.config:
                pack.config.setupSettings(settingPage)

    def fileTypes(self) -> list[FileType]:
        types = []
        for pack in self._packs:
            types.extend(pack.fileTypes())
        return types

    def _registerFileAssociations(self) -> None:
        types = []
        for pack in self._packs:
            if pack.config and not pack.config.isFileAssociationEnabled():
                continue
            types.extend(pack.fileTypes())
        file_association.register(types)

    def stop(self) -> None:
        for pack in self._packs:
            pack.stop()


featureService = FeatureService()

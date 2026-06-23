from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6.QtCore import QCoreApplication, Signal

from app.config.cfg import cfg, ConfigItem

if TYPE_CHECKING:
    from app.models.task import Task, TaskOptions
    from PySide6.QtWidgets import QWidget


@dataclass(frozen=True)
class FileType:
    extensions: tuple[str, ...]
    displayName: str
    mimeType: str
    icon: str


class TaskParser:
    priority: int = 100

    def match(self, options: TaskOptions) -> bool:
        raise NotImplementedError

    async def parse(self, options: TaskOptions) -> Task:
        raise NotImplementedError


class PackConfig:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for attrName, attrValue in cls.__dict__.items():
            if isinstance(attrValue, ConfigItem):
                setattr(cfg.__class__, f"pack_{cls.__name__}_{attrName}", attrValue)
        cfg.load()

    def setupSettings(self, settingPage) -> None:
        pass

    def isFileAssociationEnabled(self) -> bool:
        return True

    def fileAssociationToggle(self) -> Signal | None:
        return None

    def tr(self, text: str) -> str:
        return QCoreApplication.translate(self.__class__.__name__, text)


class FeaturePack:
    packId: str = ""
    config: PackConfig | None = None

    def parsers(self) -> list[TaskParser]:
        return []

    def taskCard(self, task: Task, parent=None):
        from app.view.cards.task_cards import UniversalTaskCard
        return UniversalTaskCard(task, parent)

    def draftCard(self, task: Task, parent=None):
        from app.view.cards.draft_cards import UniversalDraftCard
        return UniversalDraftCard(task, parent)

    def optionCards(self, task: Task, parent=None) -> list[QWidget]:
        return []

    def fileTypes(self) -> list[FileType]:
        return []

    def pages(self) -> list[QWidget]:
        return []

    def start(self):
        pass

    def stop(self):
        pass

    def tr(self, text: str) -> str:
        return QCoreApplication.translate(self.__class__.__name__, text)

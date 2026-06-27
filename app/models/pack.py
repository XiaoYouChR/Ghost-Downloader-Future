from __future__ import annotations

import asyncio
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

    def settingGroups(self, parent) -> list:
        return []

    def isFileAssociationEnabled(self) -> bool:
        return True

    def fileAssociationToggle(self) -> Signal | None:
        return None

    def tr(self, text: str) -> str:
        return QCoreApplication.translate(self.__class__.__name__, text)


class BinaryRuntime:
    name: str = ""
    canInstall: bool = False

    @property
    def runtimeId(self) -> str:
        cls = type(self)
        return f"{cls.__module__}.{cls.__qualname__}"

    def path(self) -> str:
        raise NotImplementedError

    async def probeVersion(self) -> str:
        path = self.path()
        if not path:
            return ""
        process = await asyncio.create_subprocess_exec(
            path, "--version",
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await process.communicate()
        if process.returncode != 0:
            return ""
        lines = stdout.decode("utf-8", errors="ignore").splitlines()
        return lines[0].strip() if lines else ""

    async def installTask(self) -> Task:
        raise NotImplementedError


class PackPage:
    icon: ...
    title: str = ""


class FeaturePack:
    packId: str = ""
    config: PackConfig | None = None
    proxySchemes: set[str] | None = None

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

    def pages(self) -> list[type[PackPage]]:
        return []

    def start(self):
        pass

    def stop(self):
        pass

    def tr(self, text: str) -> str:
        return QCoreApplication.translate(self.__class__.__name__, text)

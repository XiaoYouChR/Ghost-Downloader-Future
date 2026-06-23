from __future__ import annotations

from dataclasses import fields as dataclass_fields
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.task import Task, TaskStep


def toDict(obj: Any) -> Any:
    pass


def fromDict(data: Any, cls: type) -> Any:
    pass


def filterFields(cls: type, obj: dict[str, Any]) -> dict[str, Any]:
    allowed = {f.name for f in dataclass_fields(cls) if f.init}
    for klass in cls.__mro__:
        for name, val in vars(klass).items():
            if isinstance(val, property):
                allowed.discard(name)
    return {key: value for key, value in obj.items() if key in allowed}

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.task import Task


class CategoryService:
    def categoryOf(self, task: Task) -> str:
        pass

    def toCategory(self, task: Task) -> str:
        pass

    def folderFor(self, categoryId: str) -> str:
        pass


categoryService = CategoryService()

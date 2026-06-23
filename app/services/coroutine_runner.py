from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QThread


class CoroutineRunner(QThread):

    def run(self):
        pass

    def submit(self, work, done: Callable = None, failed: Callable = None, *args, **kwargs) -> str:
        pass

    def cancel(self, workId: str) -> bool:
        pass

    def post(self, callback: Callable, *args, **kwargs) -> None:
        pass

    def stop(self) -> None:
        pass


coroutineRunner = CoroutineRunner()

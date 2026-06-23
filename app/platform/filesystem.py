import shutil
from pathlib import Path


def toSafeFilename(name: str, fallback: str = "file", maxLength: int = 200) -> str:
    pass


def toPosixPath(path) -> str:
    pass


def deletePath(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path, ignore_errors=True)
    else:
        path.unlink(missing_ok=True)

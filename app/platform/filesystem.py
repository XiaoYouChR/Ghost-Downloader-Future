import re
import shutil
from pathlib import Path

INVALID_FILENAME_PATTERN = re.compile(r'[\x00-\x1f\x7f<>:"/\\|?*]+')
WINDOWS_RESERVED_FILENAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def toSafeFilename(name: str, fallback: str = "file", maxLength: int = 200) -> str:
    candidate = str(name or "")
    lastSep = max(candidate.rfind("/"), candidate.rfind("\\"))
    if lastSep >= 0:
        candidate = candidate[lastSep + 1:]

    candidate = INVALID_FILENAME_PATTERN.sub("_", candidate).strip().rstrip(". ")

    if not candidate or candidate in {".", ".."}:
        return fallback

    root, _, _ = candidate.partition(".")
    if root.upper() in WINDOWS_RESERVED_FILENAMES:
        candidate = f"_{candidate}"

    if 0 < maxLength < len(candidate):
        stem, dot, suffix = candidate.rpartition(".")
        if stem and dot:
            keep = maxLength - len(dot + suffix)
            candidate = f"{stem[:max(1, keep)]}{dot}{suffix}" if keep > 0 else candidate[:maxLength]
        else:
            candidate = candidate[:maxLength]

    return candidate


def toPosixPath(path) -> str:
    return str(Path(path)).replace("\\", "/")


def deletePath(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path, ignore_errors=True)
    else:
        path.unlink(missing_ok=True)

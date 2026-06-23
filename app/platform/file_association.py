from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import QCoreApplication

from app.config.constants import DESKTOP_ID
from app.config.paths import executableDir

if sys.platform == "win32":
    import ctypes
    import winreg

if TYPE_CHECKING:
    from app.models.pack import FileType


def apply(fileTypes: list[FileType]) -> None:
    try:
        if sys.platform == "win32":
            _applyWindows(fileTypes)
        elif sys.platform == "linux":
            _applyLinux(fileTypes)
    except Exception as e:
        logger.opt(exception=e).error("文件关联注册失败")


def _applyWindows(fileTypes: list[FileType]) -> None:
    command = f'"{QCoreApplication.applicationFilePath().replace("/", chr(92))}" "%1"'
    for fileType in fileTypes:
        iconPath = str(executableDir / "app" / "assets" / "file_icons" / f"{fileType.icon}.ico").replace("/", "\\")
        for ext in fileType.extensions:
            progId = f"GhostDownloader{ext}"
            for regPath, regValue in (
                (rf"Software\Classes\{progId}", fileType.displayName),
                (rf"Software\Classes\{progId}\DefaultIcon", iconPath),
                (rf"Software\Classes\{progId}\shell\open\command", command),
                (rf"Software\Classes\{ext}", progId),
            ):
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, regPath) as key:
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, regValue)
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{ext}\OpenWithProgids") as key:
                winreg.SetValueEx(key, progId, 0, winreg.REG_NONE, b"")
    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)


def _applyLinux(fileTypes: list[FileType]) -> None:
    desktopDir = Path.home() / ".local/share/applications"
    serviceDir = Path.home() / ".local/share/dbus-1/services"
    desktopFile = desktopDir / f"{DESKTOP_ID}.desktop"
    serviceFile = serviceDir / f"{DESKTOP_ID}.service"

    mimes = {ft.mimeType for ft in fileTypes}

    if not mimes:
        desktopFile.unlink(missing_ok=True)
        serviceFile.unlink(missing_ok=True)
        return

    desktopDir.mkdir(parents=True, exist_ok=True)
    serviceDir.mkdir(parents=True, exist_ok=True)
    appPath = QCoreApplication.applicationFilePath()

    desktopFile.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Ghost Downloader\n"
        f"Exec={appPath} %F\n"
        "Icon=ghost-downloader\n"
        "Terminal=false\n"
        "Categories=Network;Utility;\n"
        "DBusActivatable=true\n"
        f"MimeType={';'.join(sorted(mimes))};\n",
        encoding="utf-8",
    )
    serviceFile.write_text(
        "[D-BUS Service]\n"
        f"Name={DESKTOP_ID}\n"
        f"Exec={appPath}\n",
        encoding="utf-8",
    )

    try:
        subprocess.run(["update-desktop-database", str(desktopDir)], check=False, capture_output=True)
    except FileNotFoundError:
        pass

    for mime in mimes:
        try:
            subprocess.run(["xdg-mime", "default", f"{DESKTOP_ID}.desktop", mime], check=False, capture_output=True)
        except FileNotFoundError:
            break

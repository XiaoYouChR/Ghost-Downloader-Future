import sys

from PySide6.QtCore import QOperatingSystemVersion


def isGreaterEqualWin10() -> bool:
    cv = QOperatingSystemVersion.current()
    return sys.platform == "win32" and cv.majorVersion() >= 10


def isWin10() -> bool:
    return isGreaterEqualWin10() and sys.getwindowsversion().build < 22000


def isLessThanWin10() -> bool:
    cv = QOperatingSystemVersion.current()
    return sys.platform == "win32" and cv.majorVersion() < 10


def isGreaterEqualWin11() -> bool:
    return isGreaterEqualWin10() and sys.getwindowsversion().build >= 22000

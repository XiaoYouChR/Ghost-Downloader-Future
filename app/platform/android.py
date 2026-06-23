import sys

IS_ANDROID = hasattr(sys, "getandroidapilevel")


def nativeLibraryDir() -> str | None:
    pass


def isSystemDark() -> bool | None:
    pass

import sys
from functools import lru_cache

IS_ANDROID = hasattr(sys, "getandroidapilevel")


@lru_cache(maxsize=1)
def nativeLibraryDir() -> str | None:
    if not IS_ANDROID:
        return None
    from jnius import autoclass
    activity = autoclass("org.kivy.android.PythonActivity").mActivity
    return activity.getApplicationInfo().nativeLibraryDir


def isSystemDark() -> bool | None:
    if not IS_ANDROID:
        return None
    from jnius import autoclass
    Configuration = autoclass("android.content.res.Configuration")
    activity = autoclass("org.kivy.android.PythonActivity").mActivity
    uiMode = activity.getResources().getConfiguration().uiMode
    return (uiMode & Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES


def isStorageGranted() -> bool:
    if not IS_ANDROID:
        return True
    from jnius import autoclass
    return autoclass("android.os.Environment").isExternalStorageManager()


def requestStoragePermission() -> None:
    if not IS_ANDROID:
        return
    from jnius import autoclass
    Settings = autoclass("android.provider.Settings")
    Uri = autoclass("android.net.Uri")
    Intent = autoclass("android.content.Intent")
    activity = autoclass("org.kivy.android.PythonActivity").mActivity
    intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION)
    intent.setData(Uri.parse("package:" + activity.getPackageName()))
    activity.startActivity(intent)

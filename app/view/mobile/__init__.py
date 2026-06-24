def applyPatches() -> None:
    from .dialog_patch import patchFileDialogs, patchMessageBoxWidth
    from .fluent_patch import patchAndroidMenus, patchFluentIconRendering
    from .theme_runtime import setSystemFont, setSystemTheme
    from .touch_runtime import patchCollapsibleGroupTouch

    setSystemTheme()
    setSystemFont()
    patchFluentIconRendering()
    patchFileDialogs()
    patchMessageBoxWidth()
    patchCollapsibleGroupTouch()
    patchAndroidMenus()

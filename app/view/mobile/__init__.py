def setupAndroid() -> None:
    from .device import setupFont, setupTheme
    from .patches import (
        patchDialogWidth, patchFileDialogs, patchGroupTouch,
        patchIconRendering, patchMenus,
    )

    setupTheme()
    setupFont()
    patchIconRendering()
    patchFileDialogs()
    patchDialogWidth()
    patchGroupTouch()
    patchMenus()

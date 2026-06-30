import os
import sys
import traceback
from pathlib import Path

from loguru import logger

from app.config.paths import APP_DATA_DIR

Path(APP_DATA_DIR).mkdir(parents=True, exist_ok=True)
logger.add(f"{APP_DATA_DIR}/GhostDownloader.log", rotation="512 KB", enqueue=False)


def _exceptionHook(exceptionType, value, tb):
    info = (exceptionType, value, tb)
    logger.opt(exception=info).error("Unhandled application exception")


sys.excepthook = _exceptionHook


def setupEnvironment():
    import warnings
    from qfluentwidgets import qconfig
    from app.config.cfg import cfg
    from app.config.constants import VERSION
    from app.platform.android import nativeLibraryDir

    from app.view.qfw_patch import patchFluentLabelThemeChanged
    from app.view.components.labels import IconBodyLabel
    patchFluentLabelThemeChanged()
    qconfig.themeChanged.connect(IconBodyLabel.clearCache)
    qconfig.load(f"{APP_DATA_DIR}/UserConfig.json", cfg)
    logger.info("Ghost Downloader v{} (Android) launched", VERSION)

    if cfg.dpiScale.value != 0:
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
        os.environ["QT_SCALE_FACTOR"] = str(cfg.dpiScale.value)

    warnings.warn = logger.warning
    nativeLibraryDir()


def startApp(application):
    from PySide6.QtCore import Qt, QTranslator

    from app.config.cfg import cfg
    from app.platform.android_keepalive import keepAlive, REASON_DOWNLOAD, REASON_BROWSER, requestIgnoreBatteryOptimizations
    from app.platform.android_notification import notifyBrowserPaired, notifyBrowserTaskAdded, notifyTaskCompleted, requestNotificationPermission
    from app.services.browser_service import browserService
    from app.services.coroutine_runner import coroutineRunner
    from app.services.feature_service import featureService
    from app.services.speed_meter import speedMeter
    from app.services.task_service import taskService
    from app.signal_bus import signalBus
    from app.view.mobile.device import setupTouchScrolling
    from app.view.mobile.window import MobileMainWindow

    def exceptionHook(exceptionType, value, tb):
        _exceptionHook(exceptionType, value, tb)
        message = "".join(traceback.format_exception(exceptionType, value, tb)).rstrip()
        signalBus.exceptionCaught.emit(message)

    sys.excepthook = exceptionHook

    import app.assets.resources  # noqa: F401

    locale = cfg.language.value.value
    translator = QTranslator()
    translator.load(locale, "gd3", ".", ":/i18n")
    application.installTranslator(translator)

    coroutineRunner.start()
    featureService.load()
    from app.models.pack import PackConfig
    PackConfig.load()
    taskService.resumeSaved()
    featureService.start()

    mainWindow = MobileMainWindow()
    mainWindow.show()
    setupTouchScrolling(mainWindow)

    requestNotificationPermission()
    requestIgnoreBatteryOptimizations()

    taskService.taskCompleted.connect(notifyTaskCompleted)
    taskService.taskStarted.connect(lambda _: keepAlive.holdFor(REASON_DOWNLOAD))
    taskService.tasksAllCompleted.connect(lambda: keepAlive.release(REASON_DOWNLOAD))
    speedMeter.speedChanged.connect(keepAlive.setSpeed)

    def onBrowserTaskDraftRequested(tasks):
        for task in tasks:
            taskService.add(task)
        notifyBrowserTaskAdded(tasks)

    def onBrowserPairRequested(request):
        browserService.approvePair(request["session"], request["requestId"])
        notifyBrowserPaired(request.get("peerAddress", ""))

    browserService.taskDraftRequested.connect(onBrowserTaskDraftRequested)
    browserService.pairRequested.connect(onBrowserPairRequested)

    from app.services.aria2_rpc import aria2RpcServer
    aria2RpcServer.taskDraftRequested.connect(onBrowserTaskDraftRequested)
    if cfg.isAria2RpcEnabled.value:
        aria2RpcServer.start()
    cfg.isAria2RpcEnabled.valueChanged.connect(aria2RpcServer.setEnabled)
    cfg.aria2RpcPort.valueChanged.connect(aria2RpcServer.setPort)

    cfg.isBrowserExtensionEnabled.valueChanged.connect(
        lambda enabled: keepAlive.holdFor(REASON_BROWSER) if enabled else keepAlive.release(REASON_BROWSER)
    )
    if cfg.isBrowserExtensionEnabled.value:
        keepAlive.holdFor(REASON_BROWSER)
        browserService.start()

    def onApplicationStateChanged(state: Qt.ApplicationState) -> None:
        if state == Qt.ApplicationState.ApplicationSuspended:
            mainWindow.setUpdatesEnabled(False)
        elif state == Qt.ApplicationState.ApplicationActive:
            mainWindow.setUpdatesEnabled(True)
            mainWindow.update()

    application.applicationStateChanged.connect(onApplicationStateChanged)

    def stopApp():
        taskService.stop()
        taskService.flush()
        browserService.stop()
        aria2RpcServer.stop()
        featureService.stop()
        coroutineRunner.stop()

    application.aboutToQuit.connect(stopApp)


if __name__ == "__main__":
    from app.platform.application import SingletonApplication

    setupEnvironment()
    from app.view.mobile import setupAndroid
    setupAndroid()
    app = SingletonApplication(sys.argv, "gd3")
    startApp(app)
    sys.exit(app.exec())

import sys
import traceback

from loguru import logger

from app.config.paths import APP_DATA_DIR

logger.add(f"{APP_DATA_DIR}/GhostDownloader.log", rotation="512 KB", enqueue=True)


def _exceptionHook(exceptionType, value, tb):
    info = (exceptionType, value, tb)
    logger.opt(exception=info).error("Unhandled application exception")
    if "__compiled__" not in globals():
        sys.__excepthook__(*info)


sys.excepthook = _exceptionHook


def setupEnvironment():
    from app.config.cfg import cfg
    from app.config.constants import VERSION
    from app.platform.hidden_subprocess import setupHiddenSubprocess
    from qfluentwidgets import qconfig

    if sys.platform == "win32":
        setupHiddenSubprocess()

    import app.assets.resources  # noqa: F401
    qconfig.load(f"{APP_DATA_DIR}/UserConfig.json", cfg)
    logger.info("Ghost Downloader v{} launched", VERSION)


def startApp(application):
    from app.config.cfg import cfg
    from app.services.coroutine_runner import coroutineRunner
    from app.services.speed_meter import speedMeter
    from app.services.task_service import taskService
    from app.services.feature_service import featureService
    from app.services.browser_service import browserService
    from app.services.clipboard_listener import ClipboardListener
    from app.signal_bus import signalBus
    from app.view.windows.main_window import MainWindow

    def exceptionHook(exceptionType, value, tb):
        _exceptionHook(exceptionType, value, tb)
        message = "".join(traceback.format_exception(exceptionType, value, tb)).rstrip()
        signalBus.exceptionCaught.emit(message)

    sys.excepthook = exceptionHook

    coroutineRunner.start()
    featureService.load()
    taskService.resumeSaved()
    featureService.start()

    window = None

    def onWindowDestroyed():
        nonlocal window
        window = None

    def show() -> MainWindow:
        nonlocal window
        if window is None:
            window = MainWindow()
            window.destroyed.connect(onWindowDestroyed)
        window.show()
        from app.platform.desktop import raiseWindow
        raiseWindow(window)
        return window

    signalBus.activationRequested.connect(show)
    signalBus.openFileRequested.connect(lambda uris: show().addUrls(uris))
    signalBus.exceptionCaught.connect(lambda msg: show().alertException(msg))
    browserService.taskDraftRequested.connect(lambda tasks: show().addTasks(tasks))
    browserService.pairRequested.connect(lambda req: show().confirmPair(req))

    clipboardListener = ClipboardListener(parent=application)
    cfg.isClipboardListenerEnabled.valueChanged.connect(clipboardListener.setEnabled)
    clipboardListener.setEnabled(cfg.isClipboardListenerEnabled.value)
    clipboardListener.urlsDetected.connect(lambda urls: show().addUrls(urls))

    if cfg.isBrowserExtensionEnabled.value:
        browserService.start()
    cfg.isBrowserExtensionEnabled.valueChanged.connect(
        lambda enabled: browserService.start() if enabled else browserService.stop()
    )

    if sys.platform == "darwin":
        from app.view.shell.mac_status_item import MacStatusItem
        from app.view.shell.dock import setupDockSpeed
        statusItem = MacStatusItem()
        statusItem.show()
        speedMeter.speedChanged.connect(statusItem.setSpeed)
        application.statusItem = statusItem
        setupDockSpeed()
    else:
        from app.view.shell.tray import SystemTrayIcon
        tray = SystemTrayIcon(show().windowIcon(), parent=application)
        tray.show()

    from app.platform.android import IS_ANDROID
    if IS_ANDROID:
        from app.platform.android_notification import notifyTaskCompleted
    else:
        from app.platform.desktop_notification import init, notifyTaskCompleted
        coroutineRunner.submit(init())
    taskService.taskCompleted.connect(notifyTaskCompleted)

    from app.services.plan import plan
    taskService.tasksAllCompleted.connect(plan.trigger)

    show()

    def stopApp():
        taskService.stop()
        taskService.flush()
        browserService.stop()
        featureService.stop()
        coroutineRunner.stop()

    application.aboutToQuit.connect(stopApp)


if __name__ == "__main__":
    from app.config.constants import DESKTOP_ID
    from app.platform.application import SingletonApplication

    setupEnvironment()
    app = SingletonApplication(sys.argv, DESKTOP_ID)
    startApp(app)
    sys.exit(app.exec())

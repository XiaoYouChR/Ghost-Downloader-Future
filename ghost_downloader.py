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

    qconfig.load(f"{APP_DATA_DIR}/UserConfig.json", cfg)
    logger.info("Ghost Downloader v{} launched", VERSION)


def startApp(application):
    from app.config.cfg import cfg
    from app.services.coroutine_runner import coroutineRunner
    from app.services.task_service import taskService
    from app.services.feature_service import featureService
    from app.services.browser_service import browserService
    from app.services.clipboard_listener import ClipboardListener
    from app.signal_bus import signalBus
    from app.view.windows.main_window import MainWindow

    def exceptionHook(exceptionType, value, tb):
        _exceptionHook(exceptionType, value, tb)
        message = "".join(traceback.format_exception(exceptionType, value, tb)).rstrip()
        signalBus.catchException.emit(message)

    sys.excepthook = exceptionHook

    coroutineRunner.start()
    featureService.load()
    taskService.resumeSaved()

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
        from app.platform.file_open import raiseWindow
        raiseWindow(window)
        return window

    signalBus.showMainWindow.connect(show)
    signalBus.openFileRequested.connect(lambda uris: show().addUrls(uris))
    signalBus.catchException.connect(lambda msg: show().alertException(msg))
    browserService.taskDraftRequested.connect(lambda tasks: show().addTasks(tasks))
    browserService.pairRequested.connect(lambda req: show().confirmPair(req))

    clipboardListener = ClipboardListener(parent=application)
    cfg.enableClipboardListener.valueChanged.connect(clipboardListener.setEnabled)
    clipboardListener.setEnabled(cfg.enableClipboardListener.value)
    clipboardListener.urlsDetected.connect(lambda urls: show().addUrls(urls))

    if cfg.enableBrowserExtension.value:
        browserService.start()

    if sys.platform == "darwin":
        from app.view.shell.mac_status_item import MacStatusItem
        from app.view.shell.dock import setupDockSpeed
        statusItem = MacStatusItem()
        statusItem.show()
        taskService.speedChanged.connect(statusItem.setSpeed)
        setupDockSpeed()
    else:
        from app.view.shell.tray import SystemTrayIcon
        tray = SystemTrayIcon(show().windowIcon(), parent=application)
        tray.show()

    if not sys.platform == "darwin":
        taskService.taskCompleted.connect(lambda task: _notifyCompleted(task))

    show()

    def stopApp():
        taskService.stop()
        featureService.stop()
        taskService.flush()
        coroutineRunner.stop()

    application.aboutToQuit.connect(stopApp)


def _notifyCompleted(task):
    pass


if __name__ == "__main__":
    from app.config.constants import DESKTOP_ID
    from app.platform.application import SingletonApplication

    setupEnvironment()
    app = SingletonApplication(sys.argv, DESKTOP_ID)
    startApp(app)
    sys.exit(app.exec())

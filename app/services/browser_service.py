from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from secrets import token_urlsafe
from typing import Any, TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer, Signal, Slot
from PySide6.QtNetwork import QHostAddress
from PySide6.QtWebSockets import QWebSocketServer
from loguru import logger

from app.config.cfg import cfg
from app.config.constants import VERSION
from app.services.task_service import taskService

if TYPE_CHECKING:
    from PySide6.QtWebSockets import QWebSocket
    from app.models.task import Task, TaskOptions, ResourceTaskOptions


@dataclass
class BrowserClientSession:
    socket: QWebSocket
    authenticated: bool = False
    subscribedTasks: bool = False
    lastSnapshot: str | None = None


class MessageType(StrEnum):
    ERROR = "error"
    HELLO = "hello"
    HELLO_ACK = "hello_ack"
    PAIR_REQUEST = "pair_request"
    PAIR_RESULT = "pair_result"
    SUBSCRIBE_TASKS = "subscribe_tasks"
    TASK_SNAPSHOT = "task_snapshot"
    CREATE_TASK = "create_task"
    CREATE_TASK_RESULT = "create_task_result"
    TASK_ACTION = "task_action"
    TASK_ACTION_RESULT = "task_action_result"


class ErrorCode(StrEnum):
    BAD_REQUEST = "bad_request"
    PROTOCOL_MISMATCH = "protocol_mismatch"
    UNAUTHORIZED = "unauthorized"


class TaskAction(StrEnum):
    TOGGLE_PAUSE = "toggle_pause"
    CANCEL = "cancel"
    REDOWNLOAD = "redownload"
    OPEN_FILE = "open_file"
    OPEN_FOLDER = "open_folder"


class TaskSource(StrEnum):
    RESOURCE = "resource"
    RESOURCE_MERGE = "resource_merge"


PROTOCOL_VERSION = 1


def toStr(data: dict, key: str, default: str = "") -> str:
    value = data.get(key)
    return value if isinstance(value, str) else default


def toInt(data: dict, key: str, default: int) -> int:
    value = data.get(key)
    return value if isinstance(value, int) and value > 0 else default


class BrowserService(QObject):
    pairRequested = Signal(object)
    taskDraftRequested = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._server = QWebSocketServer(
            "Ghost Downloader Browser Socket Server",
            QWebSocketServer.SslMode.NonSecureMode,
            self,
        )
        self._server.newConnection.connect(self._onNewConnection)
        self._sessions: dict[int, BrowserClientSession] = {}
        self._snapshotTimer = QTimer(self)
        self._snapshotTimer.setInterval(1000)
        self._snapshotTimer.timeout.connect(self._broadcastSnapshots)

    @property
    def token(self) -> str:
        if not cfg.browserExtensionPairToken.value:
            cfg.set(cfg.browserExtensionPairToken, token_urlsafe(16))
        return str(cfg.browserExtensionPairToken.value)

    def regenerateToken(self) -> str:
        token = token_urlsafe(16)
        cfg.set(cfg.browserExtensionPairToken, token)
        self._closeAll()
        return token

    def start(self) -> None:
        if self._server.isListening():
            return
        if self._server.listen(QHostAddress.SpecialAddress.LocalHost, 14370):
            logger.info("Browser extension server started on port {}", self._server.serverPort())
            self._snapshotTimer.start()
        else:
            logger.error("Failed to start browser extension server: {}", self._server.errorString())

    def stop(self) -> None:
        self._closeAll()
        self._snapshotTimer.stop()
        if self._server.isListening():
            self._server.close()

    def approvePair(self, session: BrowserClientSession, requestId: str) -> None:
        self._send(session, {
            "type": MessageType.PAIR_RESULT,
            "requestId": requestId,
            "ok": True,
            "token": self.token,
            "message": "配对成功",
        })

    def rejectPair(self, session: BrowserClientSession, requestId: str) -> None:
        self._send(session, {
            "type": MessageType.PAIR_RESULT,
            "requestId": requestId,
            "ok": False,
            "message": "已拒绝配对请求",
        })

    def _toResourceTaskOptions(self, resource: dict) -> ResourceTaskOptions:
        from app.models.task import ResourceTaskOptions
        return ResourceTaskOptions(
            url=toStr(resource, "url"),
            name=toStr(resource, "filename"),
            size=toInt(resource, "size", 0),
            canUseRangeRequests=bool(resource.get("supportsRange")),
            headers=resource.get("headers") or {},
        )

    def _toTaskOptions(self, source: str, payload: dict) -> TaskOptions:
        from dataclasses import replace
        from app.models.task import MergeTaskOptions

        rawPath = payload.get("path")
        outputFolder = Path(rawPath) if rawPath else Path(cfg.downloadFolder.value)

        if source == TaskSource.RESOURCE_MERGE:
            resources = payload.get("resources") or []
            return MergeTaskOptions(
                url="gd3+ffmpeg://merge",
                outputFolder=outputFolder,
                video=self._toResourceTaskOptions(resources[0]) if len(resources) > 0 else None,
                audio=self._toResourceTaskOptions(resources[1]) if len(resources) > 1 else None,
            )

        return replace(
            self._toResourceTaskOptions(payload),
            outputFolder=outputFolder,
            subworkerCount=toInt(payload, "preBlockNum", cfg.preBlockNum.value),
        )

    def _toTaskSummary(self, task: Task) -> dict:
        progress, speed, receivedBytes = task.currentSnapshot()
        outputPath = Path(task.outputPath)
        return {
            "taskId": task.taskId,
            "name": task.name,
            "status": task.status.name.lower(),
            "progress": round(progress, 2),
            "receivedBytes": receivedBytes,
            "fileSize": task.fileSize,
            "speed": speed,
            "createdAt": task.createdAt,
            "canPause": task.canPause,
            "canOpenFile": outputPath.exists(),
            "canOpenFolder": outputPath.parent.exists(),
            "fileExt": outputPath.suffix.lstrip(".").lower(),
        }

    def _closeAll(self) -> None:
        for session in list(self._sessions.values()):
            session.socket.close()
        self._sessions.clear()

    def _send(self, session: BrowserClientSession, payload: dict) -> None:
        try:
            session.socket.sendTextMessage(json.dumps(payload, ensure_ascii=False))
        except Exception as e:
            logger.opt(exception=e).warning("Failed to send browser payload")

    def _sendError(self, session: BrowserClientSession, message: str, *,
                   requestId: str | None = None, code: ErrorCode = ErrorCode.BAD_REQUEST) -> None:
        payload: dict[str, Any] = {"type": MessageType.ERROR, "message": message, "code": code}
        if requestId:
            payload["requestId"] = requestId
        self._send(session, payload)

    def _sendResult(self, session: BrowserClientSession, messageType: MessageType,
                    requestId: str, *, ok: bool, message: str = "", taskId: str = "") -> None:
        payload: dict[str, Any] = {"type": messageType, "requestId": requestId, "ok": ok}
        if message:
            payload["message"] = message
        if taskId:
            payload["taskId"] = taskId
        self._send(session, payload)

    @Slot()
    def _onNewConnection(self) -> None:
        socket = self._server.nextPendingConnection()
        if socket is None:
            return
        self._sessions[id(socket)] = BrowserClientSession(socket=socket)
        socket.textMessageReceived.connect(self._onMessage)
        socket.disconnected.connect(self._onDisconnected)

    @Slot()
    def _onDisconnected(self) -> None:
        socket: QWebSocket = self.sender()
        if socket:
            self._sessions.pop(id(socket), None)

    @Slot()
    def _broadcastSnapshots(self) -> None:
        if not self._sessions:
            return
        tasks = sorted(taskService.tasks, key=lambda t: t.createdAt, reverse=True)
        snapshot = json.dumps({
            "type": MessageType.TASK_SNAPSHOT,
            "tasks": [self._toTaskSummary(t) for t in tasks],
        }, ensure_ascii=False)

        for session in list(self._sessions.values()):
            if not session.authenticated or not session.subscribedTasks:
                continue
            if session.lastSnapshot == snapshot:
                continue
            session.lastSnapshot = snapshot
            try:
                session.socket.sendTextMessage(snapshot)
            except Exception as e:
                logger.opt(exception=e).warning("Failed to push task snapshot")

    @Slot(str)
    def _onMessage(self, message: str) -> None:
        socket: QWebSocket = self.sender()
        session = self._sessions.get(id(socket)) if socket else None
        if session is None:
            return

        try:
            data = json.loads(message)
        except Exception:
            self._sendError(session, "无效的消息格式")
            return

        if not isinstance(data, dict):
            self._sendError(session, "无效的消息结构")
            return

        rawType = toStr(data, "type")
        try:
            msgType = MessageType(rawType)
        except ValueError:
            self._sendError(session, "未知的消息类型")
            return

        if msgType == MessageType.PAIR_REQUEST:
            self.pairRequested.emit({
                "session": session,
                "requestId": toStr(data, "requestId"),
                "protocolVersion": data.get("protocolVersion"),
                "peerAddress": f"{session.socket.peerAddress().toString()}:{session.socket.peerPort()}",
                "extensionVersion": toStr(data, "extensionVersion"),
                "clientKind": toStr(data, "clientKind"),
            })
            return

        if msgType == MessageType.HELLO:
            self._onHello(session, data)
            return

        if not session.authenticated:
            self._sendError(session, "请先完成握手认证", code=ErrorCode.UNAUTHORIZED)
            session.socket.close()
            return

        if msgType == MessageType.SUBSCRIBE_TASKS:
            session.subscribedTasks = True
            session.lastSnapshot = None
            self._broadcastSnapshots()
        elif msgType == MessageType.CREATE_TASK:
            self._onCreateTask(session, data)
        elif msgType == MessageType.TASK_ACTION:
            self._onTaskAction(session, data)

    def _onHello(self, session: BrowserClientSession, data: dict) -> None:
        requestId = toStr(data, "requestId") or None

        if toInt(data, "protocolVersion", 0) != PROTOCOL_VERSION:
            self._sendError(session, "协议版本不匹配", requestId=requestId, code=ErrorCode.PROTOCOL_MISMATCH)
            session.socket.close()
            return

        if toStr(data, "token") != self.token:
            self._sendError(session, "配对令牌无效", requestId=requestId, code=ErrorCode.UNAUTHORIZED)
            session.socket.close()
            return

        session.authenticated = True
        self._send(session, {
            "type": MessageType.HELLO_ACK,
            "protocolVersion": PROTOCOL_VERSION,
            "appVersion": VERSION,
            "capabilities": {
                "taskSnapshots": True,
                "taskActions": [a.value for a in TaskAction],
            },
        })

    def _onCreateTask(self, session: BrowserClientSession, data: dict) -> None:
        from app.services.coroutine_runner import coroutineRunner
        from app.services.feature_service import featureService

        requestId = toStr(data, "requestId")
        payload = data.get("payload")
        source = toStr(data, "source", TaskSource.RESOURCE)
        title = toStr(data, "title")

        if not requestId or not isinstance(payload, dict):
            self._sendError(session, "无效的请求")
            return

        try:
            options = self._toTaskOptions(source, payload)
        except Exception as e:
            self._sendResult(session, MessageType.CREATE_TASK_RESULT, requestId, ok=False, message=repr(e))
            return

        coroutineRunner.submit(
            featureService.parse(options),
            done=self._onTaskParsed,
            failed=self._onTaskParseFailed,
            session=session, requestId=requestId, title=title,
        )

    def _onTaskParsed(self, task: Task, session: BrowserClientSession, requestId: str, title: str) -> None:
        if title:
            task.setName(title)

        if cfg.shouldRaiseWindowOnBrowserTask.value:
            self._sendResult(session, MessageType.CREATE_TASK_RESULT, requestId, ok=False)
            self.taskDraftRequested.emit([task])
            return

        taskService.add(task)
        self._sendResult(session, MessageType.CREATE_TASK_RESULT, requestId, ok=True, taskId=task.taskId)

    def _onTaskParseFailed(self, error: str, session: BrowserClientSession, requestId: str, **_) -> None:
        self._sendResult(session, MessageType.CREATE_TASK_RESULT, requestId, ok=False, message=error)

    def _onTaskAction(self, session: BrowserClientSession, data: dict) -> None:
        from app.models.task import TaskStatus
        from app.platform.desktop import openFile, openFolder

        requestId = toStr(data, "requestId")
        taskId = toStr(data, "taskId")
        rawAction = toStr(data, "action")

        if not requestId:
            self._sendError(session, "缺少 requestId")
            return

        try:
            action = TaskAction(rawAction)
        except ValueError:
            self._sendResult(session, MessageType.TASK_ACTION_RESULT, requestId, ok=False, message="不支持的操作")
            return

        task = taskService.taskById(taskId)
        if task is None:
            self._sendResult(session, MessageType.TASK_ACTION_RESULT, requestId, ok=False, message="任务不存在")
            return

        try:
            if action == TaskAction.TOGGLE_PAUSE:
                if task.status == TaskStatus.RUNNING:
                    if not task.canPause:
                        self._sendResult(session, MessageType.TASK_ACTION_RESULT, requestId,
                                         ok=False, message="当前任务不支持暂停")
                        return
                    taskService.pause(task)
                elif task.status == TaskStatus.COMPLETED:
                    self._sendResult(session, MessageType.TASK_ACTION_RESULT, requestId,
                                     ok=False, message="任务已完成")
                    return
                else:
                    taskService.start(task)

            elif action == TaskAction.CANCEL:
                taskService.delete(task, shouldDeleteFiles=True)

            elif action == TaskAction.REDOWNLOAD:
                taskService.redownload(task)

            elif action == TaskAction.OPEN_FILE:
                path = Path(task.outputPath)
                if not path.exists():
                    self._sendResult(session, MessageType.TASK_ACTION_RESULT, requestId,
                                     ok=False, message="文件尚未生成")
                    return
                openFile(path)

            elif action == TaskAction.OPEN_FOLDER:
                path = Path(task.outputPath)
                if not path.parent.exists():
                    self._sendResult(session, MessageType.TASK_ACTION_RESULT, requestId,
                                     ok=False, message="目录不存在")
                    return
                openFolder(path)

            self._sendResult(session, MessageType.TASK_ACTION_RESULT, requestId, ok=True)

        except Exception as e:
            logger.opt(exception=e).error("Browser task action failed")
            self._sendResult(session, MessageType.TASK_ACTION_RESULT, requestId, ok=False, message=repr(e))


browserService = BrowserService()

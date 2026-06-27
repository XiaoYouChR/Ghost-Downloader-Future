from __future__ import annotations

import json
import time
import urllib.parse
from functools import reduce
from hashlib import md5
from urllib.parse import parse_qsl, urlparse

from loguru import logger
from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from app.client import buildClient
from .config import bilibiliConfig

MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52,
]

QR_GENERATE_API = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
QR_POLL_API = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
LOGIN_INFO_API = "https://api.bilibili.com/x/web-interface/nav"
LOGOUT_API = "https://passport.bilibili.com/login/exit/v2"
QR_POLL_INTERVAL = 2000
QR_UNSCANNED = 86101
QR_SCANNED = 86090
QR_EXPIRED = 86038
QR_LOGIN_SUCCESS = 1

COOKIE_ORDER = ("SESSDATA", "bili_jct", "DedeUserID", "DedeUserID__ckMd5", "sid")


def toCookie(raw: str) -> str:
    parts: dict[str, str] = {}
    for part in raw.replace("\r", ";").replace("\n", ";").split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, value = part.split("=", 1)
        name, value = name.strip(), value.strip()
        if name and value:
            parts[name] = value
    if not parts:
        return ""
    ordered = [n for n in COOKIE_ORDER if n in parts]
    extra = [n for n in parts if n not in COOKIE_ORDER]
    return "; ".join(f"{n}={parts[n]}" for n in ordered + extra)


class BilibiliAccount(QObject):
    accountChanged = Signal()
    qrStateChanged = Signal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._username = ""
        self._mid = ""
        self._vip = ""
        self._mixinKey = ""

        self._qrManager = QNetworkAccessManager(self)
        self._qrTimer = QTimer(self)
        self._qrTimer.setInterval(QR_POLL_INTERVAL)
        self._qrTimer.timeout.connect(self._pollQrStatus)
        self._qrCodeKey = ""

    @property
    def cookie(self) -> str:
        return bilibiliConfig.userCookie.value

    @property
    def isLoggedIn(self) -> bool:
        return bool(self.cookie)

    @property
    def username(self) -> str:
        return self._username

    @property
    def mid(self) -> str:
        return self._mid

    @property
    def vip(self) -> str:
        return self._vip

    def _updateWbiKeys(self, data: dict) -> None:
        wbiImg = data.get("wbi_img") or {}
        imgUrl = str(wbiImg.get("img_url") or "")
        subUrl = str(wbiImg.get("sub_url") or "")
        imgKey = imgUrl.rsplit("/", 1)[-1].split(".")[0] if imgUrl else ""
        subKey = subUrl.rsplit("/", 1)[-1].split(".")[0] if subUrl else ""
        if imgKey and subKey:
            orig = imgKey + subKey
            self._mixinKey = reduce(lambda s, i: s + orig[i], MIXIN_KEY_ENC_TAB, "")[:32]

    def signParams(self, params: dict) -> dict:
        if not self._mixinKey:
            return params
        params["wts"] = round(time.time())
        params = dict(sorted(params.items()))
        params = {k: "".join(c for c in str(v) if c not in "!'()*") for k, v in params.items()}
        query = urllib.parse.urlencode(params)
        params["w_rid"] = md5((query + self._mixinKey).encode()).hexdigest()
        return params

    # ── QR login (Qt-native, no coroutineRunner) ──

    def startQrLogin(self):
        self.cancelQrLogin()
        reply = self._qrManager.get(QNetworkRequest(QUrl(QR_GENERATE_API)))
        reply.finished.connect(lambda: self._onQrGenerated(reply))

    def cancelQrLogin(self):
        self._qrTimer.stop()
        self._qrCodeKey = ""

    def _onQrGenerated(self, reply: QNetworkReply):
        reply.deleteLater()
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self.qrStateChanged.emit(-1, f"获取二维码失败: {reply.errorString()}")
            return

        payload = json.loads(reply.readAll().data())
        if payload.get("code") not in {None, 0}:
            self.qrStateChanged.emit(-1, payload.get("message") or "获取二维码失败")
            return

        data = payload.get("data") or {}
        loginUrl = str(data.get("url") or "").strip()
        self._qrCodeKey = str(data.get("qrcode_key") or "").strip()
        if not loginUrl or not self._qrCodeKey:
            self.qrStateChanged.emit(-1, "二维码接口返回了不完整的数据")
            return

        self.qrStateChanged.emit(0, loginUrl)
        self._qrTimer.start()

    def _pollQrStatus(self):
        if not self._qrCodeKey:
            self._qrTimer.stop()
            return
        url = QUrl(f"{QR_POLL_API}?qrcode_key={self._qrCodeKey}")
        reply = self._qrManager.get(QNetworkRequest(url))
        reply.finished.connect(lambda: self._onQrPolled(reply))

    def _onQrPolled(self, reply: QNetworkReply):
        reply.deleteLater()
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self._qrTimer.stop()
            self.qrStateChanged.emit(-1, f"轮询扫码状态失败: {reply.errorString()}")
            return

        payload = json.loads(reply.readAll().data())
        if payload.get("code") not in {None, 0}:
            self._qrTimer.stop()
            self.qrStateChanged.emit(-1, payload.get("message") or "轮询扫码状态失败")
            return

        data = payload.get("data") or {}
        statusCode = int(data.get("code", -1))
        statusMessage = str(data.get("message") or "")

        if statusCode in {QR_UNSCANNED, QR_SCANNED}:
            self.qrStateChanged.emit(statusCode, statusMessage)
            return

        self._qrTimer.stop()

        if statusCode == QR_EXPIRED:
            self.qrStateChanged.emit(QR_EXPIRED, "")
            return

        if statusCode == 0:
            successUrl = str(data.get("url") or "")
            items: dict[str, str] = {}
            for name, value in parse_qsl(urlparse(successUrl).query, keep_blank_values=False):
                if name in COOKIE_ORDER and value:
                    items[name] = value
            if items:
                cookie = toCookie("; ".join(f"{k}={v}" for k, v in items.items()))
                self.setCookie(cookie)
                self.fetchAccountInfo()
                self.qrStateChanged.emit(QR_LOGIN_SUCCESS, "")
            else:
                self.qrStateChanged.emit(-1, "登录成功，但未能提取到有效 Cookie")
            return

        self.qrStateChanged.emit(-1, statusMessage or f"未知扫码状态：{statusCode}")

    # ── cookie / logout / account info (wreq via coroutineRunner) ──

    def setCookie(self, cookie: str):
        from app.config.cfg import cfg
        from app.services.coroutine_runner import coroutineRunner

        cookie = toCookie(cookie)
        oldCookie = self.cookie
        if oldCookie and oldCookie != cookie:
            def onDone(_):
                cfg.set(bilibiliConfig.userCookie, cookie)
                self.accountChanged.emit()
            coroutineRunner.submit(self._logout(), done=onDone, failed=onDone)
        else:
            cfg.set(bilibiliConfig.userCookie, cookie)
            self.accountChanged.emit()

    def logout(self):
        from app.services.coroutine_runner import coroutineRunner
        coroutineRunner.submit(self._logout(), done=self._onLogoutDone, failed=self._onLogoutFailed)

    def fetchAccountInfo(self):
        from app.services.coroutine_runner import coroutineRunner
        coroutineRunner.submit(self._fetchAccountInfo(), done=self._onAccountInfoDone, failed=self._onAccountInfoFailed)

    async def fetchWbiKeys(self) -> None:
        if self._mixinKey:
            return
        client = buildClient()
        try:
            response = await client.get(LOGIN_INFO_API)
            response.raise_for_status()
            payload = await response.json()
            self._updateWbiKeys(payload.get("data") or {})
        finally:
            client.close()

    async def _logout(self) -> bool:
        cookie = self.cookie
        parts: dict[str, str] = {}
        for part in cookie.split(";"):
            part = part.strip()
            if "=" in part:
                name, value = part.split("=", 1)
                parts[name.strip()] = value.strip()

        required = ("DedeUserID", "bili_jct", "SESSDATA")
        if any(not parts.get(n) for n in required):
            return True

        client = buildClient(headers={
            "cookie": cookie,
            "origin": "https://www.bilibili.com",
            "referer": "https://www.bilibili.com/",
        })
        try:
            response = await client.post(LOGOUT_API, data={
                "biliCSRF": parts["bili_jct"],
                "gourl": "https://www.bilibili.com/",
            })
            response.raise_for_status()
            contentType = (response.headers.get("content-type") or b"").decode().lower()
            if "application/json" not in contentType:
                return True

            payload = await response.json()
            if payload.get("code") == 0 and payload.get("status") is True:
                return True

            raise ValueError(payload.get("message") or "退出登录失败")
        finally:
            client.close()

    async def _fetchAccountInfo(self) -> dict:
        cookie = self.cookie
        if not cookie:
            return {"isLoggedIn": False, "uname": ""}

        client = buildClient(headers={"cookie": cookie})
        try:
            response = await client.get(LOGIN_INFO_API)
            response.raise_for_status()
            payload = await response.json()
            data = payload.get("data") or {}

            if payload.get("code") == -101 or not data.get("isLogin"):
                return {"isLoggedIn": False, "uname": ""}

            if payload.get("code") not in {None, 0}:
                raise ValueError(payload.get("message") or "获取登录信息失败")

            vipPayload = data.get("vip") or {}
            vipStatus = int(data.get("vipStatus") or vipPayload.get("status") or 0)
            if vipStatus != 1:
                vipText = "未开通"
            else:
                vipLabel = ((vipPayload.get("label") or {}).get("text")
                            or (data.get("vip_label") or {}).get("text") or "").strip()
                if vipLabel:
                    vipText = vipLabel
                else:
                    vipType = int(data.get("vipType") or vipPayload.get("type") or 0)
                    vipText = {1: "月度大会员", 2: "年度大会员"}.get(vipType, "大会员")

            return {
                "isLoggedIn": True,
                "uname": str(data.get("uname") or "").strip(),
                "mid": str(data.get("mid") or ""),
                "vip": vipText,
                "wbiData": data,
            }
        finally:
            client.close()

    def _onLogoutDone(self, shouldClear: bool):
        if shouldClear:
            from app.config.cfg import cfg
            cfg.set(bilibiliConfig.userCookie, "")
            self._username = ""
            self._mid = ""
            self._vip = ""
            self.accountChanged.emit()

    def _onLogoutFailed(self, error: str):
        self.accountChanged.emit()

    def _onAccountInfoDone(self, result: dict):
        self._username = result.get("uname", "")
        self._mid = result.get("mid", "")
        self._vip = result.get("vip", "")
        wbiData = result.get("wbiData")
        if wbiData:
            self._updateWbiKeys(wbiData)
        self.accountChanged.emit()

    def _onAccountInfoFailed(self, error: str):
        pass


bilibiliAccount = BilibiliAccount()

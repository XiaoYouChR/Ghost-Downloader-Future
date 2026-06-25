from __future__ import annotations

import asyncio
from urllib.parse import parse_qsl, urlparse

from PySide6.QtCore import QObject, Signal

from app.client import buildClient
from .config import bilibiliConfig

QR_GENERATE_API = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
QR_POLL_API = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
LOGIN_INFO_API = "https://api.bilibili.com/x/web-interface/nav"
LOGOUT_API = "https://passport.bilibili.com/login/exit/v2"
QR_POLL_INTERVAL = 2.0
QR_UNSCANNED = 86101
QR_SCANNED = 86090

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
        self._polling = False

    @property
    def cookie(self) -> str:
        return bilibiliConfig.userCookie.value

    @property
    def isLoggedIn(self) -> bool:
        return bool(self.cookie)

    @property
    def username(self) -> str:
        return self._username

    def startQrLogin(self):
        from app.services.coroutine_runner import coroutineRunner
        self._polling = True
        coroutineRunner.submit(self._pollQrLogin(), done=self._onQrLoginDone, failed=self._onQrLoginFailed)

    def cancelQrLogin(self):
        self._polling = False

    def setCookie(self, cookie: str):
        bilibiliConfig.userCookie.value = toCookie(cookie)
        self.accountChanged.emit()

    def logout(self):
        from app.services.coroutine_runner import coroutineRunner
        coroutineRunner.submit(self._logout(), done=self._onLogoutDone, failed=self._onLogoutFailed)

    def fetchAccountInfo(self):
        from app.services.coroutine_runner import coroutineRunner
        coroutineRunner.submit(self._fetchAccountInfo(), done=self._onAccountInfoDone, failed=self._onAccountInfoFailed)

    async def _pollQrLogin(self) -> str:
        from app.services.coroutine_runner import coroutineRunner

        client = buildClient()
        try:
            response = await client.get(QR_GENERATE_API)
            response.raise_for_status()
            payload = await response.json()
            if payload.get("code") not in {None, 0}:
                raise ValueError(payload.get("message") or "获取二维码失败")

            data = payload.get("data") or {}
            loginUrl = str(data.get("url") or "").strip()
            qrCodeKey = str(data.get("qrcode_key") or "").strip()
            if not loginUrl or not qrCodeKey:
                raise ValueError("二维码接口返回了不完整的数据")

            coroutineRunner.post(self.qrStateChanged.emit, 0, loginUrl)

            while self._polling:
                await asyncio.sleep(QR_POLL_INTERVAL)
                if not self._polling:
                    return ""

                response = await client.get(QR_POLL_API, params={"qrcode_key": qrCodeKey})
                response.raise_for_status()
                payload = await response.json()
                data = payload.get("data") or {}
                statusCode = int(data.get("code", -1))
                statusMessage = str(data.get("message") or "")

                if statusCode in {QR_UNSCANNED, QR_SCANNED}:
                    coroutineRunner.post(self.qrStateChanged.emit, statusCode, statusMessage)
                    continue

                if statusCode == 0:
                    items = {c.name(): c.value() for c in response.cookies if c.name() and c.value()}
                    successUrl = str(data.get("url") or "")
                    if not any(n in items for n in COOKIE_ORDER):
                        for name, value in parse_qsl(urlparse(successUrl).query, keep_blank_values=False):
                            if name in COOKIE_ORDER and value:
                                items[name] = value
                    if items:
                        return toCookie("; ".join(f"{k}={v}" for k, v in items.items()))

                return ""

            return ""
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

            return {"isLoggedIn": True, "uname": str(data.get("uname") or "").strip()}
        finally:
            client.close()

    def _onQrLoginDone(self, cookie: str):
        self._polling = False
        if cookie:
            self.setCookie(cookie)
            self.fetchAccountInfo()

    def _onQrLoginFailed(self, error: Exception):
        self._polling = False

    def _onLogoutDone(self, shouldClear: bool):
        if shouldClear:
            bilibiliConfig.userCookie.value = ""
            self._username = ""
            self.accountChanged.emit()

    def _onLogoutFailed(self, error: Exception):
        pass

    def _onAccountInfoDone(self, result: dict):
        self._username = result.get("uname", "")
        self.accountChanged.emit()

    def _onAccountInfoFailed(self, error: Exception):
        pass


bilibiliAccount = BilibiliAccount()

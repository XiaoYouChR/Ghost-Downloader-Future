from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from app.client import buildClient, toEmulation
from app.config.cfg import cfg
from app.models.pack import FeaturePack, TaskParser
from app.models.task import Task, TaskOptions
from app.platform.filesystem import toSafeFilename
from .account import bilibiliAccount
from .config import bilibiliConfig
from .task import BilibiliAudioStep, BilibiliMergeStep, BilibiliVideoStep


class BilibiliParser(TaskParser):
    priority = 50

    def match(self, options: TaskOptions) -> bool:
        hostname = (urlparse(options.url).hostname or "").lower()
        return hostname == "bilibili.com" or hostname.endswith(".bilibili.com")

    async def parse(self, options: TaskOptions) -> Task:
        url = options.url
        subworkerCount = options.subworkerCount
        outputFolder = options.outputFolder

        parsed = urlparse(url)
        referer = parsed._replace(netloc="www.bilibili.com").geturl() if (
            (parsed.hostname or "").lower() != "bilibili.com"
        ) else url

        headers = {
            **dict(options.headers),
            "referer": referer,
        }
        cookie = bilibiliAccount.cookie
        if cookie:
            headers["cookie"] = cookie

        emulation = toEmulation(
            options.clientProfile or cfg.clientProfile.value,
            options.sourceUserAgent,
        )
        client = buildClient(emulation=emulation, headers=headers)

        try:
            videoIdMatch = re.match(r"/video/(BV[a-zA-Z0-9]+|av\d+)", parsed.path)
            if not videoIdMatch:
                raise ValueError("不是有效的 Bilibili 视频链接")
            videoId = videoIdMatch.group(1)

            pageParam = parse_qs(parsed.query).get("p", [""])[0].strip()
            selectedPages: list[int] | None = None
            if pageParam:
                selectedPages = []
                for part in pageParam.split(","):
                    part = part.strip()
                    if "-" in part:
                        start, end = map(int, part.split("-", 1))
                        if start > end:
                            start, end = end, start
                        selectedPages.extend(range(start, end + 1))
                    else:
                        selectedPages.append(int(part))

            viewApiUrl = (
                f"https://api.bilibili.com/x/web-interface/view?avid={videoId[2:]}"
                if videoId.startswith("av")
                else f"https://api.bilibili.com/x/web-interface/view?bvid={videoId}"
            )

            response = await client.get(viewApiUrl)
            response.raise_for_status()
            viewPayload = await response.json()
            if viewPayload.get("code") not in {None, 0}:
                raise ValueError(viewPayload.get("message") or "获取 Bilibili 视频信息失败")

            viewData = viewPayload.get("data") or {}
            pages = list(viewData.get("pages") or [])
            if not pages:
                raise ValueError("未获取到视频分P信息")

            if selectedPages is None:
                selectedPages = list(range(1, len(pages) + 1))
            selectedPages = [p for p in dict.fromkeys(selectedPages) if 1 <= p <= len(pages)]
            if not selectedPages:
                raise ValueError("未找到有效的分P编号")

            videoTitle = str(viewData.get("title", "")).strip() or "bilibili_video"
            requestedQuality = bilibiliConfig.defaultQuality.value
            baseName = toSafeFilename(videoTitle, fallback="bilibili_video")

            def buildSuffix(pageNumber: int, pagePart: str) -> str:
                if len(selectedPages) <= 1:
                    return ""
                suffix = f" - P{pageNumber}"
                if pagePart and pagePart != baseName:
                    suffix += f" {pagePart}"
                return suffix

            if len(selectedPages) == 1:
                page = pages[selectedPages[0] - 1]
                suffix = buildSuffix(selectedPages[0], str(page.get("part", "")).strip())
                taskName = f"{baseName}{suffix}.mp4"
            else:
                taskName = f"{baseName}.mp4"

            fnval = 16
            if bilibiliConfig.shouldIncludeHdr.value:
                fnval |= 64
            if bilibiliConfig.shouldIncludeDolby.value:
                fnval |= 256 | 512
            if requestedQuality == 128:
                fnval |= 1024
            if requestedQuality == 120:
                fnval |= 128

            totalSize = 0
            resolvedPages = []

            for pageNumber in selectedPages:
                page = pages[pageNumber - 1]
                pagePart = str(page.get("part", "")).strip()
                cid = int(page["cid"])

                playApiUrl = (
                    f"https://api.bilibili.com/x/player/wbi/playurl?avid={videoId[2:]}&cid={cid}&qn={requestedQuality}&fnval={fnval}&fourk=1"
                    if videoId.startswith("av")
                    else f"https://api.bilibili.com/x/player/wbi/playurl?bvid={videoId}&cid={cid}&qn={requestedQuality}&fnval={fnval}&fourk=1"
                )

                response = await client.get(playApiUrl)
                response.raise_for_status()
                playPayload = await response.json()
                if playPayload.get("code") not in {None, 0}:
                    raise ValueError(playPayload.get("message") or "获取 Bilibili 音视频流失败")

                pageData = playPayload.get("data") or {}
                videoUrl = self._selectStream(
                    pageData.get("dash", {}).get("video") or [],
                    requestedQuality,
                    list(pageData.get("accept_quality") or []),
                )
                audioUrl = self._selectStream(
                    pageData.get("dash", {}).get("audio") or [],
                )
                if not videoUrl or not audioUrl:
                    raise ValueError("未能解析出完整的音视频下载链接")

                videoSize = await self._fetchSize(client, videoUrl, headers)
                audioSize = await self._fetchSize(client, audioUrl, headers)
                totalSize += videoSize + audioSize

                resolvedPages.append({
                    "pageNumber": pageNumber,
                    "pagePart": pagePart,
                    "videoUrl": videoUrl,
                    "audioUrl": audioUrl,
                    "videoSize": videoSize,
                    "audioSize": audioSize,
                })

            task = Task(
                name=taskName,
                url=url,
                packId="bili",
                fileSize=totalSize,
                outputFolder=outputFolder,
            )

            for index, info in enumerate(resolvedPages):
                suffix = buildSuffix(info["pageNumber"], info["pagePart"])
                stepBase = index * 3

                task.addStep(BilibiliVideoStep(
                    stepIndex=stepBase + 1,
                    url=info["videoUrl"],
                    fileSize=info["videoSize"],
                    headers=dict(headers),

                    subworkerCount=subworkerCount,
                    canUseRangeRequests=True,
                    pageIndex=index,
                    pageSuffix=suffix,
                ))
                task.addStep(BilibiliAudioStep(
                    stepIndex=stepBase + 2,
                    url=info["audioUrl"],
                    fileSize=info["audioSize"],
                    headers=dict(headers),

                    subworkerCount=subworkerCount,
                    canUseRangeRequests=True,
                    pageIndex=index,
                    pageSuffix=suffix,
                ))
                task.addStep(BilibiliMergeStep(
                    stepIndex=stepBase + 3,
                    pageIndex=index,
                    pageSuffix=suffix,
                ))

            return task
        finally:
            client.close()

    def _selectStream(
        self,
        streams: list[dict],
        quality: int | None = None,
        acceptQuality: list[int] | None = None,
    ) -> str:
        if not streams:
            raise ValueError("Bilibili 返回结果中不存在可用的媒体流")

        def streamUrl(s: dict) -> str:
            url = s.get("baseUrl") or s.get("base_url")
            if isinstance(url, str) and url:
                return url
            backup = s.get("backupUrl") or s.get("backup_url") or []
            if isinstance(backup, list):
                for item in backup:
                    if isinstance(item, str) and item:
                        return item
            return ""

        if quality is not None and acceptQuality:
            resolved = quality
            if resolved not in acceptQuality:
                resolved = max(acceptQuality) if bilibiliConfig.alternativeQuality.value == "max" else min(acceptQuality)
            for s in streams:
                if s.get("id") == resolved and streamUrl(s):
                    return streamUrl(s)

        for s in streams:
            url = streamUrl(s)
            if url:
                return url

        raise ValueError("未找到可用的媒体流")

    async def _fetchSize(self, client, url: str, headers: dict) -> int:
        response = await client.get(url, headers={**headers, "range": "bytes=0-0"})
        try:
            response.raise_for_status()
            head = {k.decode().lower(): v.decode() for k, v in response.headers}
            if response.status.as_int() == 206 and "content-range" in head:
                _, _, total = head["content-range"].rpartition("/")
                if total != "*":
                    return int(total)
            raise ValueError("音视频流不支持范围请求，当前实现无法下载")
        finally:
            response.close()


class BilibiliPack(FeaturePack):
    packId = "bili"
    config = bilibiliConfig

    def parsers(self):
        return [BilibiliParser()]

    def start(self):
        bilibiliAccount.fetchAccountInfo()

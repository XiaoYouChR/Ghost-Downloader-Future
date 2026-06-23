async def fetchTorrentBytes(magnetUri: str, webTrackers: list[str]) -> bytes:
    from .session import btSession
    btSession.open()
    ...

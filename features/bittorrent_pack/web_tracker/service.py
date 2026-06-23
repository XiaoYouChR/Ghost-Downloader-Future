class TrackerService:
    def mergedTrackers(self) -> list[str]: ...

    async def refresh(self) -> tuple[int, int]: ...


trackerService = TrackerService()

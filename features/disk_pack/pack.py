from pathlib import Path

from app.config.cfg import cfg, proxies
from app.models.pack import FeaturePack
from app.platform.filesystem import toPosixPath
from .task import ExtractStep, InstallStep, InstallTask


class DiskPack(FeaturePack):
    packId = "disk"


def buildBinaryInstallTask(
    packId: str,
    installFolder: Path,
    executableNames: list[str],
    *,
    url: str,
    fileName: str,
    fileSize: int,
    name: str = "",
) -> InstallTask:
    from features.http_pack.task import HttpTaskStep

    archivePath = toPosixPath(installFolder / fileName)
    extractFolder = toPosixPath(installFolder / ".extracting")

    task = InstallTask(
        name=name or fileName,
        url=url,
        packId=packId,
        fileSize=fileSize,
        outputFolder=installFolder,
        usesSlot=False,
        installFolder=str(installFolder),
    )
    task.addStep(HttpTaskStep(
        stepIndex=1,
        url=url,
        fileSize=fileSize,
        headers=dict(cfg.defaultRequestHeaders.value),
        proxies=proxies() or {},
        subworkerCount=cfg.preBlockNum.value,
        canUseRangeRequests=True,
        outputFile=archivePath,
    ))
    task.addStep(ExtractStep(
        stepIndex=2,
        archivePath=archivePath,
        outputFolder=extractFolder,
        archiveSize=fileSize,
    ))
    task.addStep(InstallStep(
        stepIndex=3,
        sourceFolder=extractFolder,
        installFolder=toPosixPath(installFolder),
        archivePath=archivePath,
        executableNames=executableNames,
    ))
    return task

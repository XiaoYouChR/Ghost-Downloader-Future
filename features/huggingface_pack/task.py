from __future__ import annotations

from dataclasses import dataclass

from app.models.task import Task, TaskFile, TaskStep

from features.http_pack.task import HttpTaskStep


@dataclass(kw_only=True)
class HuggingFaceFile(TaskFile):
    downloadUrl: str = ""


@dataclass(kw_only=True)
class HuggingFaceStep(HttpTaskStep):
    fileIndex: int = -1

    @classmethod
    def fromFile(cls, file: TaskFile, task: Task) -> TaskStep:
        from app.config.cfg import cfg
        hfFile: HuggingFaceFile = file
        return cls(
            stepIndex=file.index + 1,
            url=hfFile.downloadUrl,
            fileSize=file.size,
            headers=task.steps[0].headers if task.steps else {},
            subworkerCount=cfg.preBlockNum.value,
            canUseRangeRequests=file.size > 0,
            fileIndex=file.index,
            outputFile=str(task.outputFolder / file.relativePath),
        )


@dataclass(kw_only=True, eq=False)
class HuggingFaceTask(Task):
    packId: str = "huggingface"
    fileType = HuggingFaceFile
    stepType = HuggingFaceStep
    repoId: str = ""
    repoType: str = "model"
    revision: str = "main"

    @property
    def countSelected(self) -> int:
        return sum(1 for f in self.files if f.selected) if self.files else 0

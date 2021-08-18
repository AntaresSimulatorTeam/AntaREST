from typing import Optional, List

from antarest.core.tasks.model import TaskJob


class TaskJobRepository:
    def save(self, task: TaskJob) -> None:
        pass

    def get(self, id: str) -> Optional[TaskJob]:
        pass

    def list(self) -> List[TaskJob]:
        pass

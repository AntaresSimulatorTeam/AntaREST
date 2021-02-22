from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from uuid import UUID

from antarest.common.config import Config
from antarest.launcher.model import JobResult


class ILauncher(ABC):
    def __init__(self, config: Config):
        self.config = config

    @abstractmethod
    def run_study(self, study_path: Path, version: str) -> UUID:
        pass

    @abstractmethod
    def get_result(self, uuid: UUID) -> Optional[JobResult]:
        pass

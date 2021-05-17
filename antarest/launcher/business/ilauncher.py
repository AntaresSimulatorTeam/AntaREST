from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable
from uuid import UUID

from antarest.common.config import Config
from antarest.common.requests import RequestParameters
from antarest.launcher.model import JobResult
from antarest.storage.service import StorageService


class ILauncher(ABC):
    def __init__(self, config: Config, storage_service: StorageService):
        self.config = config
        self.storage_service = storage_service

    @abstractmethod
    def run_study(
        self, study_uuid: str, version: str, params: RequestParameters
    ) -> UUID:
        pass

    @abstractmethod
    def add_callback(self, callback: Callable[[JobResult], None]) -> None:
        pass

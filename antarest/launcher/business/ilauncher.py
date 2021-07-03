from abc import ABC, abstractmethod
from typing import Callable, List
from uuid import UUID

from antarest.common.config import Config
from antarest.common.requests import RequestParameters
from antarest.launcher.model import JobStatus
from antarest.storage.service import StorageService


class LauncherInitException(Exception):
    pass


class ILauncher(ABC):
    def __init__(self, config: Config, storage_service: StorageService):
        self.config = config
        self.storage_service = storage_service
        self.callbacks: List[Callable[[str, JobStatus], None]] = []

    @abstractmethod
    def run_study(
        self, study_uuid: str, version: str, params: RequestParameters
    ) -> UUID:
        pass

    def add_statusupdate_callback(
        self, callback: Callable[[str, JobStatus], None]
    ) -> None:
        self.callbacks.append(callback)

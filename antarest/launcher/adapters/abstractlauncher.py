from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, NamedTuple, Optional, Dict

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import (
    Event,
    EventType,
    EventChannelDirectory,
    IEventBus,
)
from antarest.core.model import JSON
from antarest.core.requests import RequestParameters
from antarest.launcher.model import JobStatus, LogType


class LauncherInitException(Exception):
    pass


class LauncherCallbacks(NamedTuple):
    # args: job_id, job status, message, output_id
    update_status: Callable[
        [str, JobStatus, Optional[str], Optional[str]], None
    ]
    # args: job_id, study_id, study_export_path, launcher_params
    export_study: Callable[[str, str, Path, Optional[JSON]], None]
    append_before_log: Callable[[str, str], None]
    append_after_log: Callable[[str, str], None]
    get_job_study_id: Callable[[str], Optional[str]]
    # args: job_id, output_path, additional_logs
    import_output: Callable[[str, Path, Dict[str, Path]], Optional[str]]


class AbstractLauncher(ABC):
    def __init__(
        self,
        config: Config,
        callbacks: LauncherCallbacks,
        event_bus: IEventBus,
    ):
        self.config = config
        self.callbacks = callbacks
        self.event_bus = event_bus

    @abstractmethod
    def run_study(
        self,
        study_uuid: str,
        job_id: str,
        version: str,
        launcher_parameters: Optional[JSON],
        params: RequestParameters,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_log(self, job_id: str, log_type: LogType) -> Optional[str]:
        raise NotImplementedError()

    @abstractmethod
    def kill_job(self, job_id: str) -> None:
        raise NotImplementedError()

    def create_update_log(
        self, job_id: str, study_id: str
    ) -> Callable[[str], None]:
        def update_log(log_line: str) -> None:
            self.event_bus.push(
                Event(
                    type=EventType.STUDY_JOB_LOG_UPDATE,
                    payload={
                        "log": log_line,
                        "job_id": job_id,
                        "study_id": study_id,
                    },
                    channel=EventChannelDirectory.JOB_LOGS + job_id,
                )
            )

        return update_log

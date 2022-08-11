from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, NamedTuple, Optional, Dict, List

from antarest.core.config import Config
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import (
    Event,
    EventType,
    EventChannelDirectory,
    IEventBus,
)
from antarest.core.requests import RequestParameters
from antarest.launcher.adapters.log_parser import LaunchProgressDTO, LogParser
from antarest.launcher.model import JobStatus, LogType, LauncherParametersDTO


class LauncherInitException(Exception):
    pass


class LauncherCallbacks(NamedTuple):
    # args: job_id, job status, message, output_id
    update_status: Callable[
        [str, JobStatus, Optional[str], Optional[str]], None
    ]
    # args: job_id, study_id, study_export_path, launcher_params
    export_study: Callable[[str, str, Path, LauncherParametersDTO], None]
    append_before_log: Callable[[str, str], None]
    append_after_log: Callable[[str, str], None]
    # args: job_id, output_path, additional_logs
    import_output: Callable[[str, Path, Dict[str, List[Path]]], Optional[str]]


class AbstractLauncher(ABC):
    def __init__(
        self,
        config: Config,
        callbacks: LauncherCallbacks,
        event_bus: IEventBus,
        cache: ICache,
    ):
        self.config = config
        self.callbacks = callbacks
        self.event_bus = event_bus
        self.cache = cache

    @abstractmethod
    def run_study(
        self,
        study_uuid: str,
        job_id: str,
        version: str,
        launcher_parameters: LauncherParametersDTO,
        params: RequestParameters,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_log(self, job_id: str, log_type: LogType) -> Optional[str]:
        raise NotImplementedError()

    @abstractmethod
    def kill_job(self, job_id: str) -> None:
        raise NotImplementedError()

    def create_update_log(self, job_id: str) -> Callable[[str], None]:
        def update_log(log_line: str) -> None:
            self.event_bus.push(
                Event(
                    type=EventType.STUDY_JOB_LOG_UPDATE,
                    payload={
                        "log": log_line,
                        "job_id": job_id,
                    },
                    channel=EventChannelDirectory.JOB_LOGS + job_id,
                )
            )

            launch_progress_json = (
                self.cache.get(id=f"Launch_Progress_{job_id}") or {}
            )
            launch_progress_dto = LaunchProgressDTO.parse_obj(
                launch_progress_json
            )

            if LogParser.update_progress(log_line, launch_progress_dto):
                self.event_bus.push(
                    Event(
                        type=EventType.LAUNCH_PROGRESS,
                        payload={
                            "progress": launch_progress_dto.progress,
                            "message": "",
                        },
                        channel=EventChannelDirectory.JOB_LOGS + job_id,
                    )
                )
                self.cache.put(
                    f"Launch_Progress_{job_id}", launch_progress_dto.dict()
                )

        return update_log

    def get_launch_progress(self, job_id: str) -> float:
        launch_progress_json = self.cache.get(
            id=f"Launch_Progress_{job_id}"
        ) or {"progress": 0}
        return launch_progress_json.get("progress", 0)

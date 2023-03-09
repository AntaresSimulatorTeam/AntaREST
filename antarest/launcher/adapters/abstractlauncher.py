import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Dict, List, NamedTuple, Optional

from antarest.core.config import Config
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import (
    Event,
    EventChannelDirectory,
    EventType,
    IEventBus,
)
from antarest.core.model import PermissionInfo, PublicMode
from antarest.core.requests import RequestParameters
from antarest.launcher.adapters.log_parser import LaunchProgressDTO, LogParser
from antarest.launcher.model import JobStatus, LauncherParametersDTO, LogType


class LauncherInitException(Exception):
    """
    Exception raised during local or SLURM launcher initialisation
    when a required parameter is not set in the application configuration.

    In Docker environment, the configuration path is `/resources/application.yaml`.
    """

    def __init__(self, reason: str) -> None:
        from antarest.core.utils import utils

        if config_path := (
            os.getenv("ANTAREST_CONF") or utils.get_default_config_path()
        ):
            msg = f"Invalid configuration '{config_path}': {reason}"
        else:
            msg = f"Invalid configuration: {reason}"
        super().__init__(msg)


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
                    permissions=PermissionInfo(public_mode=PublicMode.READ),
                    channel=EventChannelDirectory.JOB_LOGS + job_id,
                )
            )

            launch_progress_json = (
                self.cache.get(id=f"Launch_Progress_{job_id}") or {}
            )
            launch_progress_dto = LaunchProgressDTO.parse_obj(
                launch_progress_json
            )
            progress_updated = False
            for line in log_line.split("\n"):
                progress_updated = (
                    LogParser.update_progress(line, launch_progress_dto)
                    or progress_updated
                )
            if progress_updated:
                self.event_bus.push(
                    Event(
                        type=EventType.LAUNCH_PROGRESS,
                        payload={
                            "id": job_id,
                            "progress": launch_progress_dto.progress,
                            "message": "",
                        },
                        permissions=PermissionInfo(
                            public_mode=PublicMode.READ
                        ),
                        channel=EventChannelDirectory.JOB_STATUS + job_id,
                    )
                )
                self.cache.put(
                    f"Launch_Progress_{job_id}", launch_progress_dto.dict()
                )

        return update_log

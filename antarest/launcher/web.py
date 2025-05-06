# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import http
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter
from fastapi.exceptions import HTTPException

from antarest.core.config import Config, InvalidConfigurationError, Launcher
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.utils.web import APITag
from antarest.launcher.model import (
    JobCreationDTO,
    JobResultDTO,
    LauncherEnginesDTO,
    LauncherLoadDTO,
    LauncherParametersDTO,
    LogType,
)
from antarest.launcher.service import LauncherService
from antarest.launcher.ssh_client import SlurmError
from antarest.login.auth import Auth

logger = logging.getLogger(__name__)

DEFAULT_MAX_LATEST_JOBS = 200


class UnknownSolverConfig(HTTPException):
    """
    Exception raised during solver versions retrieval when
    the name of the launcher is not "default", "slurm" or "local".
    """

    def __init__(self, solver: str) -> None:
        super().__init__(
            http.HTTPStatus.UNPROCESSABLE_ENTITY,
            f"Unknown solver configuration: '{solver}'",
        )


def create_launcher_api(service: LauncherService, config: Config) -> APIRouter:
    auth = Auth(config)
    bp = APIRouter(prefix="/v1/launcher", dependencies=[auth.required()])

    @bp.post(
        "/run/{study_id}",
        tags=[APITag.launcher],
        summary="Run study",
        response_model=JobCreationDTO,
    )
    def run(
        study_id: str,
        launcher: Optional[str] = None,
        launcher_parameters: LauncherParametersDTO = LauncherParametersDTO(),
        version: Optional[str] = None,
    ) -> Any:
        logger.info(f"Launching study {study_id} with options {launcher_parameters}")
        selected_launcher = launcher if launcher is not None else config.launcher.default

        return JobCreationDTO(
            job_id=service.run_study(
                study_id,
                selected_launcher,
                launcher_parameters,
                version,
            )
        )

    @bp.get(
        "/jobs",
        tags=[APITag.launcher],
        summary="Retrieve jobs",
        response_model=List[JobResultDTO],
    )
    def get_job(study: Optional[str] = None, filter_orphans: bool = True, latest: Optional[int] = None) -> Any:
        logger.info(f"Fetching execution jobs for study {study or '<all>'}")
        return [job.to_dto() for job in service.get_jobs(study, filter_orphans, latest)]

    @bp.get(
        "/jobs/{job_id}/logs",
        tags=[APITag.launcher],
        summary="Retrieve job logs from job id",
    )
    def get_job_log(job_id: str, log_type: LogType = LogType.STDOUT) -> Any:
        logger.info(f"Fetching logs for job {job_id}")
        return service.get_log(job_id, log_type)

    @bp.get(
        "/jobs/{job_id}/output",
        tags=[APITag.launcher],
        summary="Export job output",
        response_model=FileDownloadTaskDTO,
    )
    def export_job_output(job_id: str) -> Any:
        logger.info(f"Exporting output for job {job_id}")
        return service.download_output(job_id)

    @bp.post(
        "/jobs/{job_id}/kill",
        tags=[APITag.launcher],
        summary="Kill job",
    )
    def kill_job(
        job_id: str,
    ) -> Any:
        logger.info(f"Killing job {job_id}")

        return service.kill_job(job_id=job_id).to_dto()

    @bp.get(
        "/jobs/{job_id}",
        tags=[APITag.launcher],
        summary="Retrieve job info from job id",
        response_model=JobResultDTO,
    )
    def get_result(job_id: UUID) -> Any:
        logger.info(f"Fetching job info {job_id}")
        return service.get_result(job_id).to_dto()

    @bp.get(
        "/jobs/{job_id}/progress",
        tags=[APITag.launcher],
        summary="Retrieve job progress from job id",
        response_model=int,
    )
    def get_progress(job_id: str) -> Any:
        logger.info(f"Fetching job progress of job {job_id}")
        return int(service.get_launch_progress(job_id))

    @bp.delete(
        "/jobs/{job_id}",
        tags=[APITag.launcher],
        summary="Remove job",
        responses={204: {"description": "Job removed"}},
    )
    def remove_result(job_id: str) -> None:
        logger.info(f"Removing job {job_id}")
        service.remove_job(job_id)

    @bp.get(
        "/engines",
        tags=[APITag.launcher],
        summary="Retrieve available engines",
        response_model=LauncherEnginesDTO,
    )
    def get_engines() -> Any:
        logger.info("Listing launch engines")
        return LauncherEnginesDTO(engines=service.get_launchers())

    @bp.get(
        "/load",
        tags=[APITag.launcher],
        summary="Get the SLURM cluster or local machine load",
        response_model=LauncherLoadDTO,
    )
    def get_load(launcher_id: str = "local") -> LauncherLoadDTO:
        logger.info("Fetching launcher load")
        try:
            return service.get_load(launcher_id)
        except SlurmError as e:
            logger.warning(e, exc_info=e)
            args = {
                "allocatedCpuRate": 0.0,
                "clusterLoadRate": 0.0,
                "nbQueuedJobs": 0,
                "launcherStatus": f"FAILED: {e}",
            }
            return LauncherLoadDTO(**args)

    @bp.get(
        "/versions",
        tags=[APITag.launcher],
        summary="Get list of supported solver versions",
        response_model=List[str],
    )
    def get_solver_versions(solver: str = Launcher.DEFAULT) -> List[str]:
        """
        Get list of supported solver versions defined in the configuration.

        Args:
        - `solver`: name of the configuration to read: "default", "slurm" or "local".
        """
        logger.info(f"Fetching the list of solver versions for the '{solver}' configuration")
        return service.get_solver_versions(solver)

    # noinspection SpellCheckingInspection
    @bp.get(
        "/nbcores",  # We avoid "nb_cores" and "nb-cores" in endpoints
        tags=[APITag.launcher],
        summary="Retrieving Min, Default, and Max Core Count",
        response_model=Dict[str, int],
    )
    def get_nb_cores(launcher: str = Launcher.DEFAULT) -> Dict[str, int]:
        """
        Retrieve the numer of cores of the launcher.

        Args:
        - `launcher`: name of the configuration to read: "slurm" or "local".
          If "default" is specified, retrieve the configuration of the default launcher.

        Returns:
        - "min": min number of cores
        - "defaultValue": default number of cores
        - "max": max number of cores
        """
        logger.info(f"Fetching the number of cores for the '{launcher}' configuration")
        try:
            return service.config.launcher.get_nb_cores(launcher).to_json()
        except InvalidConfigurationError:
            raise UnknownSolverConfig(launcher)

    # noinspection SpellCheckingInspection
    @bp.get(
        "/time-limit",
        tags=[APITag.launcher],
        summary="Retrieve the time limit for a job (in hours)",
    )
    def get_time_limit(launcher: str = Launcher.LOCAL) -> Dict[str, int]:
        """
        Retrieve the time limit for a job (in hours) of the given launcher: "local" or "slurm".

        If a jobs exceed this time limit, SLURM kills the job and it is considered failed.

        Args:
        - `launcher`: name of the configuration to read: "slurm" or "local".
          If "default" is specified, retrieve the configuration of the default launcher.

        Returns:
        - "min": min allowed time limit
        - "defaultValue": default time limit
        - "max": max allowed time limit
        """
        logger.info(f"Fetching the time limit for the '{launcher}' configuration")
        try:
            return service.config.launcher.get_time_limit(launcher).to_json()
        except InvalidConfigurationError:
            raise UnknownSolverConfig(launcher)

    return bp

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

from fastapi import APIRouter, Depends, Query
from fastapi.exceptions import HTTPException

from antarest.core.config import Config, InvalidConfigurationError, Launcher
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.jwt import JWTUser
from antarest.core.requests import RequestParameters
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


LauncherQuery = Query(
    default=Launcher.DEFAULT,
    openapi_examples={
        "Default launcher": {
            "description": "Default solver (auto-detected)",
            "value": "default",
        },
        "SLURM launcher": {
            "description": "SLURM solver configuration",
            "value": "slurm",
        },
        "Local launcher": {
            "description": "Local solver configuration",
            "value": "local",
        },
    },
)


def create_launcher_api(service: LauncherService, config: Config) -> APIRouter:
    bp = APIRouter(prefix="/v1/launcher")

    auth = Auth(config)

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
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(f"Launching study {study_id} with options {launcher_parameters}")
        selected_launcher = launcher if launcher is not None else config.launcher.default

        params = RequestParameters(user=current_user)
        return JobCreationDTO(
            job_id=service.run_study(
                study_id,
                selected_launcher,
                launcher_parameters,
                params,
                version,
            )
        )

    @bp.get(
        "/jobs",
        tags=[APITag.launcher],
        summary="Retrieve jobs",
        response_model=List[JobResultDTO],
    )
    def get_job(
        study: Optional[str] = None,
        filter_orphans: bool = True,
        latest: Optional[int] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(f"Fetching execution jobs for study {study or '<all>'}")
        params = RequestParameters(user=current_user)
        return [job.to_dto() for job in service.get_jobs(study, params, filter_orphans, latest)]

    @bp.get(
        "/jobs/{job_id}/logs",
        tags=[APITag.launcher],
        summary="Retrieve job logs from job id",
    )
    def get_job_log(
        job_id: str,
        log_type: LogType = LogType.STDOUT,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(f"Fetching logs for job {job_id}")
        params = RequestParameters(user=current_user)
        return service.get_log(job_id, log_type, params)

    @bp.get(
        "/jobs/{job_id}/output",
        tags=[APITag.launcher],
        summary="Export job output",
        response_model=FileDownloadTaskDTO,
    )
    def export_job_output(
        job_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(f"Exporting output for job {job_id}")
        params = RequestParameters(user=current_user)
        return service.download_output(job_id, params)

    @bp.post(
        "/jobs/{job_id}/kill",
        tags=[APITag.launcher],
        summary="Kill job",
    )
    def kill_job(
        job_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(f"Killing job {job_id}")

        params = RequestParameters(user=current_user)
        return service.kill_job(
            job_id=job_id,
            params=params,
        ).to_dto()

    @bp.get(
        "/jobs/{job_id}",
        tags=[APITag.launcher],
        summary="Retrieve job info from job id",
        response_model=JobResultDTO,
    )
    def get_result(job_id: UUID, current_user: JWTUser = Depends(auth.get_current_user)) -> Any:
        logger.info(f"Fetching job info {job_id}")
        params = RequestParameters(user=current_user)
        return service.get_result(job_id, params).to_dto()

    @bp.get(
        "/jobs/{job_id}/progress",
        tags=[APITag.launcher],
        summary="Retrieve job progress from job id",
        response_model=int,
    )
    def get_progress(job_id: str, current_user: JWTUser = Depends(auth.get_current_user)) -> Any:
        logger.info(f"Fetching job progress of job {job_id}")
        params = RequestParameters(user=current_user)
        return int(service.get_launch_progress(job_id, params))

    @bp.delete(
        "/jobs/{job_id}",
        tags=[APITag.launcher],
        summary="Remove job",
        responses={204: {"description": "Job removed"}},
    )
    def remove_result(job_id: str, current_user: JWTUser = Depends(auth.get_current_user)) -> None:
        logger.info(f"Removing job {job_id}")
        params = RequestParameters(user=current_user)
        service.remove_job(job_id, params)

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
    def get_load() -> LauncherLoadDTO:
        logger.info("Fetching launcher load")
        try:
            return service.get_load()
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
    def get_solver_versions(solver: Launcher = Launcher.DEFAULT) -> List[str]:
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
    def get_nb_cores(launcher: Launcher = Launcher.DEFAULT) -> Dict[str, int]:
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
    def get_time_limit(launcher: Launcher = LauncherQuery) -> Dict[str, int]:
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

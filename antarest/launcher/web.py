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

import logging
from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter

from antarest.core.config import Config
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.utils.web import APITag
from antarest.launcher.model import (
    JobCreationDTO,
    JobResultDTO,
    LauncherListDTO,
    LauncherLoadDTO,
    LauncherParametersDTO,
    LogType,
    SolverPresets,
    SolverPresetsCreation,
    SolverPresetsUpdate,
)
from antarest.launcher.service import LauncherService
from antarest.launcher.ssh_client import SlurmError
from antarest.login.auth import Auth

logger = logging.getLogger(__name__)

DEFAULT_MAX_LATEST_JOBS = 200


def create_launcher_api(service: LauncherService, config: Config) -> APIRouter:
    auth = Auth(config)
    bp = APIRouter(prefix="/v1/launcher", tags=[APITag.launcher], dependencies=[auth.required()])

    @bp.post(
        "/run/{study_id}",
        summary="Run study",
        response_model=JobCreationDTO,
    )
    def run(
        study_id: str,
        launcher: Optional[str] = None,
        launcher_parameters: LauncherParametersDTO = LauncherParametersDTO(),
        solver_presets_id: Optional[str] = None,
        version: Optional[str] = None,
    ) -> Any:
        logger.info(f"Launching study {study_id} with options {launcher_parameters}")
        selected_launcher = launcher if launcher is not None else config.launcher.default

        return JobCreationDTO(
            job_id=service.run_study(
                study_id,
                selected_launcher,
                launcher_parameters,
                solver_presets_id,
                version,
            )
        )

    @bp.get(
        "/jobs",
        summary="Retrieve jobs",
        response_model=List[JobResultDTO],
    )
    def get_job(study: Optional[str] = None, filter_orphans: bool = True, latest: Optional[int] = None) -> Any:
        logger.info(f"Fetching execution jobs for study {study or '<all>'}")
        return [job.to_dto() for job in service.get_jobs(study, filter_orphans, latest)]

    @bp.get(
        "/jobs/{job_id}/logs",
        summary="Retrieve job logs from job id",
    )
    def get_job_log(job_id: str, log_type: LogType = LogType.STDOUT) -> Any:
        logger.info(f"Fetching logs for job {job_id}")
        return service.get_log(job_id, log_type)

    @bp.get(
        "/jobs/{job_id}/output",
        summary="Export job output",
        response_model=FileDownloadTaskDTO,
    )
    def export_job_output(job_id: str) -> Any:
        logger.info(f"Exporting output for job {job_id}")
        return service.download_output(job_id)

    @bp.post(
        "/jobs/{job_id}/kill",
        summary="Kill job",
    )
    def kill_job(
        job_id: str,
    ) -> Any:
        logger.info(f"Killing job {job_id}")

        return service.kill_job(job_id=job_id).to_dto()

    @bp.get(
        "/jobs/{job_id}",
        summary="Retrieve job info from job id",
        response_model=JobResultDTO,
    )
    def get_result(job_id: UUID) -> Any:
        logger.info(f"Fetching job info {job_id}")
        return service.get_result(job_id).to_dto()

    @bp.get(
        "/jobs/{job_id}/progress",
        summary="Retrieve job progress from job id",
        response_model=int,
    )
    def get_progress(job_id: str) -> Any:
        logger.info(f"Fetching job progress of job {job_id}")
        return int(service.get_launch_progress(job_id))

    @bp.delete(
        "/jobs/{job_id}",
        summary="Remove job",
        responses={204: {"description": "Job removed"}},
    )
    def remove_result(job_id: str) -> None:
        logger.info(f"Removing job {job_id}")
        service.remove_job(job_id)

    @bp.get(
        "/launchers",
        summary="Retrieve configured launchers",
        response_model=LauncherListDTO,
    )
    def get_launchers() -> Any:
        logger.info("Listing launchers")
        return service.get_launchers()

    @bp.get(
        "/load",
        summary="Get the SLURM cluster or local machine load",
        response_model=LauncherLoadDTO,
    )
    def get_load(launcher_id: Optional[str] = None) -> LauncherLoadDTO:
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
        summary="Get list of supported solver versions",
        response_model=List[str],
    )
    def get_solver_versions(solver: Optional[str] = None) -> List[str]:
        """
        Get list of supported solver versions defined in the configuration.

        Args:
        - `solver`: name of the configuration to read.
          If no solver is specified, retrieve the configuration of the default launcher.
        """
        logger.info(f"Fetching the list of solver versions for the '{solver}' configuration")
        return service.get_solver_versions(solver)

    @bp.post(
        "/solver-presets",
        summary="Create new solver presets",
    )
    def create_solver_presets(solver_presets_creation: SolverPresetsCreation) -> SolverPresets:
        logger.info("Creating new solver presets")
        return service.create_solver_presets(solver_presets_creation)

    @bp.get(
        "/solver-presets/{solver_presets_id}",
        summary="Retrieve solver presets by ID",
    )
    def get_solver_presets(solver_presets_id: str) -> SolverPresets:
        logger.info(f"Retrieving solver presets for ID {solver_presets_id}")
        return service.get_solver_presets(solver_presets_id)

    @bp.get(
        "/solver-presets",
        summary="Retrieve all solver presets",
    )
    def get_solver_presets_list() -> List[SolverPresets]:
        logger.info("Retrieving solver presets")
        return service.get_solver_presets_list()

    @bp.put(
        "/solver-presets/{solver_presets_id}",
        summary="Update an existing solver preset",
    )
    def update_solver_presets(solver_presets_id: str, solver_presets_update: SolverPresetsUpdate) -> SolverPresets:
        logger.info(f"Updating solver preset for ID {solver_presets_id}")
        return service.update_solver_presets(solver_presets_id, solver_presets_update)

    @bp.delete(
        "/solver-presets/{solver_presets_id}",
        summary="Delete a solver preset",
    )
    def delete_solver_presets(solver_presets_id: str) -> None:
        logger.info(f"Deleting solver preset for ID {solver_presets_id}")
        service.delete_solver_presets(solver_presets_id)

    return bp

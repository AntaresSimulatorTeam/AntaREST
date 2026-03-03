# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import Field

from antarest.core.api_types import SanitizedStr, UuidStr
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
    )
    def run(
        study_id: UuidStr,
        launcher: Optional[SanitizedStr] = None,
        launcher_parameters: LauncherParametersDTO = LauncherParametersDTO(),
        solver_presets_id: Optional[SanitizedStr] = None,
        version: Optional[SanitizedStr] = None,
    ) -> JobCreationDTO:
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
    )
    def get_job(
        study: Optional[SanitizedStr] = None, filter_orphans: bool = True, latest: Optional[int] = None
    ) -> List[JobResultDTO]:
        logger.info(f"Fetching execution jobs for study {study or '<all>'}")
        return [job.to_dto() for job in service.get_jobs(study, filter_orphans, latest)]

    @bp.get(
        "/jobs/{job_id}/logs",
        summary="Retrieve job logs from job id",
    )
    def get_job_log(job_id: SanitizedStr, log_type: LogType = LogType.STDOUT) -> str | None:
        logger.info(f"Fetching logs for job {job_id}")
        return service.get_log(job_id, log_type)

    @bp.get(
        "/jobs/{job_id}/output",
        summary="Export job output",
    )
    def export_job_output(job_id: SanitizedStr) -> FileDownloadTaskDTO:
        logger.info(f"Exporting output for job {job_id}")
        return service.download_output(job_id)

    @bp.post(
        "/jobs/{job_id}/kill",
        summary="Kill job",
    )
    def kill_job(
        job_id: SanitizedStr,
    ) -> JobResultDTO:
        logger.info(f"Killing job {job_id}")

        return service.kill_job(job_id=job_id).to_dto()

    @bp.get(
        "/jobs/{job_id}",
        summary="Retrieve job info from job id",
    )
    def get_result(job_id: UUID) -> JobResultDTO:
        logger.info(f"Fetching job info {job_id}")
        return service.get_result(job_id).to_dto()

    @bp.get(
        "/jobs/{job_id}/progress",
        summary="Retrieve job progress from job id",
    )
    def get_progress(job_id: SanitizedStr) -> int:
        logger.info(f"Fetching job progress of job {job_id}")
        return int(service.get_launch_progress(job_id))

    @bp.delete(
        "/jobs/{job_id}",
        summary="Remove job",
        responses={204: {"description": "Job removed"}},
    )
    def remove_result(job_id: SanitizedStr) -> None:
        logger.info(f"Removing job {job_id}")
        service.remove_job(job_id)

    @bp.get(
        "/launchers",
        summary="Retrieve configured launchers",
    )
    def get_launchers() -> LauncherListDTO:
        logger.info("Listing launchers")
        return service.get_launchers()

    @bp.get(
        "/load",
        summary="Get the SLURM cluster or local machine load",
    )
    def get_load(launcher_id: Optional[SanitizedStr] = None) -> LauncherLoadDTO:
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
        summary="Get list of supported solver versions for the specified launcher",
        response_description='List of supported solver versions formatted as "880" for 8.8.',
        deprecated=True,
    )
    def get_solver_versions(
        launcher_id: SanitizedStr | None = None,
        solver: Annotated[SanitizedStr | None, Query(deprecated=True)] = None,
    ) -> Annotated[list[str], Field(examples=[["820", "880", "920"]])]:
        """
        Get list of supported solver versions for the specified launcher.

        **DEPRECATED**: Use GET /launchers instead, which includes versions for each launcher.

        Args:
           launcher_id: ID of the considered launcher. If no launcher is specified, returns solvers
                        of the default launcher.
        """
        launcher_id = launcher_id or solver
        launcher_msg = f"launcher '{launcher_id}'" if launcher_id else "default launcher"
        logger.info(f"Fetching the list of solver versions for {launcher_msg}")
        return service.get_solver_versions(launcher_id)

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
    def get_solver_presets(solver_presets_id: SanitizedStr) -> SolverPresets:
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
    def update_solver_presets(
        solver_presets_id: SanitizedStr, solver_presets_update: SolverPresetsUpdate
    ) -> SolverPresets:
        logger.info(f"Updating solver preset for ID {solver_presets_id}")
        return service.update_solver_presets(solver_presets_id, solver_presets_update)

    @bp.delete(
        "/solver-presets/{solver_presets_id}",
        summary="Delete a solver preset",
    )
    def delete_solver_presets(solver_presets_id: SanitizedStr) -> None:
        logger.info(f"Deleting solver preset for ID {solver_presets_id}")
        service.delete_solver_presets(solver_presets_id)

    return bp

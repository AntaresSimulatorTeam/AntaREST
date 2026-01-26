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
import io
import logging
from typing import Sequence

import polars as pl
from fastapi import APIRouter, File, UploadFile
from starlette.responses import Response

from antarest.core.config import Config
from antarest.core.model import StudyPermissionType
from antarest.core.serde.json import to_json
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.study.business.model.xpansion_model import (
    XpansionAdequacyCriterion,
    XpansionCandidate,
    XpansionCandidateCreation,
    XpansionResourceFileType,
    XpansionSettings,
    XpansionSettingsUpdate,
)
from antarest.study.service import StudyService

logger = logging.getLogger(__name__)


def create_xpansion_routes(study_service: StudyService, config: Config) -> APIRouter:
    """
    Endpoint implementation for xpansion studies management

    Args:
        study_service: study service facade to handle request
        config: main server configuration
    """
    auth = Auth(config)
    bp = APIRouter(prefix="/v1", tags=[APITag.xpansion_study_management], dependencies=[auth.required()])

    @bp.post(
        "/studies/{uuid}/extensions/xpansion",
        summary="Create Xpansion Configuration",
    )
    def create_xpansion_configuration(uuid: str) -> None:
        logger.info(f"Creating Xpansion Configuration for study {uuid}")
        study_service.create_xpansion_configuration(uuid=uuid)

    @bp.delete(
        "/studies/{uuid}/extensions/xpansion",
        summary="Delete Xpansion Configuration",
    )
    def delete_xpansion_configuration(uuid: str) -> None:
        logger.info(f"Deleting Xpansion Configuration for study {uuid}")
        study_service.delete_xpansion_configuration(uuid=uuid)

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/settings",
        summary="Get Xpansion Settings",
    )
    def get_settings(uuid: str) -> XpansionSettings:
        logger.info(f"Fetching Xpansion Settings of the study {uuid}")
        return study_service.get_xpansion_settings(uuid=uuid)

    @bp.put(
        "/studies/{uuid}/extensions/xpansion/settings",
        summary="Update Xpansion Settings",
    )
    def update_settings(uuid: str, xpansion_settings: XpansionSettingsUpdate) -> XpansionSettings:
        logger.info(f"Updating Xpansion Settings of Study {uuid}")
        return study_service.update_xpansion_settings(uuid, xpansion_settings)

    @bp.put(
        "/studies/{uuid}/extensions/xpansion/settings/additional-constraints",
        summary="Update Xpansion Settings Additional Constraints",
    )
    def update_additional_constraints_settings(uuid: str, filename: str = "") -> XpansionSettings:
        logger.info(f"Updating Xpansion Settings of Study {uuid} with additional constraints {filename}")
        return study_service.update_xpansion_constraints_settings(uuid, filename)

    @bp.post(
        "/studies/{uuid}/extensions/xpansion/candidates",
        summary="Create Xpansion Candidate",
    )
    def add_candidate(uuid: str, xpansion_candidate: XpansionCandidateCreation) -> XpansionCandidate:
        logger.info(f"Adding new candidate {xpansion_candidate.model_dump(by_alias=True)} to study {uuid}")
        return study_service.add_candidate(uuid, xpansion_candidate)

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/candidates/{candidate_name}",
        summary="Get Xpansion Candidate",
    )
    def get_candidate(uuid: str, candidate_name: str) -> XpansionCandidate:
        logger.info("Fetching study list")
        return study_service.get_candidate(uuid, candidate_name)

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/candidates",
        summary="Get Xpansion Candidates",
    )
    def get_candidates(uuid: str) -> Sequence[XpansionCandidate]:
        logger.info("Fetching study list")
        return study_service.get_candidates(uuid)

    @bp.put(
        "/studies/{uuid}/extensions/xpansion/candidates/{candidate_name}",
        summary="Update Xpansion Candidate",
    )
    def update_candidate(
        uuid: str, candidate_name: str, xpansion_candidate: XpansionCandidateCreation
    ) -> XpansionCandidate:
        logger.info(f"Updating xpansion candidate {xpansion_candidate.name} of the study {uuid}")
        return study_service.replace_xpansion_candidate(uuid, candidate_name, xpansion_candidate)

    @bp.delete(
        "/studies/{uuid}/extensions/xpansion/candidates/{candidate_name}",
        summary="Delete Xpansion Candidate",
    )
    def delete_candidate(uuid: str, candidate_name: str) -> None:
        logger.info(f"Deleting candidate {candidate_name} of the study {uuid}")
        study_service.delete_xpansion_candidate(uuid, candidate_name)

    @bp.post(
        "/studies/{uuid}/extensions/xpansion/resources/{resource_type}",
        summary="Add Xpansion resource file",
    )
    def add_resource(uuid: str, resource_type: XpansionResourceFileType, file: UploadFile = File(...)) -> None:
        logger.info(f"Add xpansion {resource_type} files in the study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.xpansion_manager.add_resource(study_interface, resource_type, file)

    @bp.delete(
        "/studies/{uuid}/extensions/xpansion/resources/{resource_type}/{filename}",
        summary="Delete Xpansion resource file",
    )
    def delete_resource(uuid: str, resource_type: XpansionResourceFileType, filename: str) -> None:
        logger.info(f"Deleting xpansion {resource_type} file from the study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.xpansion_manager.delete_resource(study_interface, resource_type, filename)

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/resources/{resource_type}/{filename}",
        summary="Getting Xpansion resource file content",
    )
    def get_resource_content(uuid: str, resource_type: XpansionResourceFileType, filename: str) -> Response:
        logger.info(f"Getting xpansion {resource_type} file {filename} from the study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)

        output = study_service.xpansion_manager.get_resource_content(study_interface, resource_type, filename)

        if isinstance(output, pl.DataFrame):
            buffer = io.BytesIO()
            output.to_pandas().to_json(buffer, orient="split")
            return Response(content=buffer.getvalue(), media_type="application/json")

        return Response(content=to_json(output.decode("utf-8")), media_type="application/json")

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/resources/{resource_type}",
        summary="Getting all Xpansion resources files",
    )
    def list_resources(uuid: str, resource_type: XpansionResourceFileType) -> list[str]:
        logger.info(f"Getting xpansion {resource_type} resources files from the study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.xpansion_manager.list_resources(study_interface, resource_type)

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/adequacy_criterion",
        summary="Gets the Xpansion adequacy criterion configuration",
    )
    def get_adequacy_criterion(uuid: str) -> XpansionAdequacyCriterion:
        logger.info(f"Getting xpansion adequacy criterion from the study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.xpansion_manager.get_adequacy_criterion(study_interface)

    @bp.put(
        "/studies/{uuid}/extensions/xpansion/adequacy_criterion",
        summary="Replace the Xpansion adequacy criterion configuration",
    )
    def update_security_criterion(uuid: str, criterion: XpansionAdequacyCriterion) -> XpansionAdequacyCriterion:
        logger.info(f"Updates xpansion adequacy criterion from the study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.xpansion_manager.replace_adequacy_criterion(study_interface, criterion)

    return bp

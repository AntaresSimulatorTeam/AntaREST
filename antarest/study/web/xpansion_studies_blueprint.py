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
from typing import Any, Sequence

from fastapi import APIRouter, Depends, File, UploadFile
from starlette.responses import Response

from antarest.core.config import Config
from antarest.core.model import JSON, StudyPermissionType
from antarest.core.serde.json import to_json
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.study.business.model.xpansion_model import (
    GetXpansionSettings,
    XpansionCandidateDTO,
    XpansionResourceFileType,
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
    bp = APIRouter(prefix="/v1", dependencies=[Depends(auth.get_current_user)])

    @bp.post(
        "/studies/{uuid}/extensions/xpansion",
        tags=[APITag.xpansion_study_management],
        summary="Create Xpansion Configuration",
    )
    def create_xpansion_configuration(uuid: str) -> Any:
        logger.info(f"Creating Xpansion Configuration for study {uuid}")
        study_service.create_xpansion_configuration(uuid=uuid)

    @bp.delete(
        "/studies/{uuid}/extensions/xpansion",
        tags=[APITag.xpansion_study_management],
        summary="Delete Xpansion Configuration",
    )
    def delete_xpansion_configuration(uuid: str) -> Any:
        logger.info(f"Deleting Xpansion Configuration for study {uuid}")
        study_service.delete_xpansion_configuration(uuid=uuid)

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/settings",
        tags=[APITag.xpansion_study_management],
        summary="Get Xpansion Settings",
    )
    def get_settings(uuid: str) -> GetXpansionSettings:
        logger.info(f"Fetching Xpansion Settings of the study {uuid}")
        return study_service.get_xpansion_settings(uuid=uuid)

    @bp.put(
        "/studies/{uuid}/extensions/xpansion/settings",
        tags=[APITag.xpansion_study_management],
        summary="Update Xpansion Settings",
    )
    def update_settings(uuid: str, xpansion_settings: XpansionSettingsUpdate) -> GetXpansionSettings:
        logger.info(f"Updating Xpansion Settings Of Study {uuid}")
        return study_service.update_xpansion_settings(uuid, xpansion_settings)

    @bp.put(
        "/studies/{uuid}/extensions/xpansion/settings/additional-constraints",
        tags=[APITag.xpansion_study_management],
        summary="Update Xpansion Settings Additional Constraints",
    )
    def update_additional_constraints_settings(
        uuid: str,
        filename: str = "",
    ) -> GetXpansionSettings:
        logger.info(f"Updating Xpansion Settings Of Study {uuid} with additional constraints {filename}")
        return study_service.update_xpansion_constraints_settings(uuid, filename)

    @bp.post(
        "/studies/{uuid}/extensions/xpansion/candidates",
        tags=[APITag.xpansion_study_management],
        summary="Create Xpansion Candidate",
    )
    def add_candidate(
        uuid: str,
        xpansion_candidate_dto: XpansionCandidateDTO,
    ) -> XpansionCandidateDTO:
        logger.info(f"Adding new candidate {xpansion_candidate_dto.model_dump(by_alias=True)} to study {uuid}")
        return study_service.add_candidate(uuid, xpansion_candidate_dto)

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/candidates/{candidate_name}",
        tags=[APITag.xpansion_study_management],
        summary="Get Xpansion Candidate",
    )
    def get_candidate(
        uuid: str,
        candidate_name: str,
    ) -> XpansionCandidateDTO:
        logger.info("Fetching study list")
        return study_service.get_candidate(uuid, candidate_name)

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/candidates",
        tags=[APITag.xpansion_study_management],
        summary="Get Xpansion Candidates",
    )
    def get_candidates(
        uuid: str,
    ) -> Sequence[XpansionCandidateDTO]:
        logger.info("Fetching study list")
        return study_service.get_candidates(uuid)

    @bp.put(
        "/studies/{uuid}/extensions/xpansion/candidates/{candidate_name}",
        tags=[APITag.xpansion_study_management],
        summary="Update Xpansion Candidate",
    )
    def update_candidate(
        uuid: str,
        candidate_name: str,
        xpansion_candidate_dto: XpansionCandidateDTO,
    ) -> Any:
        logger.info(f"Updating xpansion candidate {xpansion_candidate_dto.name} of the study {uuid}")
        return study_service.update_xpansion_candidate(uuid, candidate_name, xpansion_candidate_dto)

    @bp.delete(
        "/studies/{uuid}/extensions/xpansion/candidates/{candidate_name}",
        tags=[APITag.xpansion_study_management],
        summary="Delete Xpansion Candidate",
    )
    def delete_candidate(
        uuid: str,
        candidate_name: str,
    ) -> Any:
        logger.info(f"Deleting candidate {candidate_name} of the study {uuid}")
        return study_service.delete_xpansion_candidate(uuid, candidate_name)

    @bp.post(
        "/studies/{uuid}/extensions/xpansion/resources/{resource_type}",
        tags=[APITag.xpansion_study_management],
        summary="Add Xpansion resource file",
    )
    def add_resource(
        uuid: str,
        resource_type: XpansionResourceFileType,
        file: UploadFile = File(...),
    ) -> None:
        logger.info(f"Add xpansion {resource_type} files in the study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.xpansion_manager.add_resource(study_interface, resource_type, file)

    @bp.delete(
        "/studies/{uuid}/extensions/xpansion/resources/{resource_type}/{filename}",
        tags=[APITag.xpansion_study_management],
        summary="Delete Xpansion resource file",
    )
    def delete_resource(
        uuid: str,
        resource_type: XpansionResourceFileType,
        filename: str,
    ) -> Any:
        logger.info(f"Deleting xpansion {resource_type} file from the study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.WRITE)
        study_interface = study_service.get_study_interface(study)
        return study_service.xpansion_manager.delete_resource(study_interface, resource_type, filename)

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/resources/{resource_type}/{filename}",
        tags=[APITag.xpansion_study_management],
        summary="Getting Xpansion resource file content",
    )
    def get_resource_content(
        uuid: str,
        resource_type: XpansionResourceFileType,
        filename: str,
    ) -> Any:
        logger.info(f"Getting xpansion {resource_type} file {filename} from the study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        output: JSON | bytes | str = study_service.xpansion_manager.get_resource_content(
            study_interface, resource_type, filename
        )

        if isinstance(output, bytes):
            try:
                # try to decode string
                output = output.decode("utf-8")
            except (AttributeError, UnicodeDecodeError):
                pass

        json_response = to_json(output)
        return Response(content=json_response, media_type="application/json")

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/resources/{resource_type}",
        tags=[APITag.xpansion_study_management],
        summary="Getting all Xpansion resources files",
    )
    def list_resources(
        uuid: str,
        resource_type: XpansionResourceFileType,
    ) -> Any:
        logger.info(f"Getting xpansion {resource_type} resources files from the study {uuid}")
        study = study_service.check_study_access(uuid, StudyPermissionType.READ)
        study_interface = study_service.get_study_interface(study)
        return study_service.xpansion_manager.list_resources(study_interface, resource_type)

    return bp

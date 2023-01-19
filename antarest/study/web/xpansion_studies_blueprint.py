import json
import logging
from typing import Any, List, Optional, Union

from fastapi import APIRouter, Depends, UploadFile, File
from starlette.responses import Response

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.model import StudyPermissionType, JSON
from antarest.core.requests import RequestParameters
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.study.business.xpansion_management import (
    XpansionSettingsDTO,
    XpansionCandidateDTO,
    XpansionResourceFileType,
)
from antarest.study.service import StudyService

logger = logging.getLogger(__name__)


def create_xpansion_routes(
    study_service: StudyService, config: Config
) -> APIRouter:
    """
    Endpoint implementation for xpansion studies management
    Args:
        study_service: study service facade to handle request
        ftm: file transfer manager
        config: main server configuration

    Returns:

    """
    bp = APIRouter(prefix="/v1")
    auth = Auth(config)

    @bp.post(
        "/studies/{uuid}/extensions/xpansion",
        tags=[APITag.xpansion_study_management],
        summary="Create Xpansion Configuration",
    )
    def create_xpansion_configuration(
        uuid: str,
        file: Optional[UploadFile] = File(None),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Creating Xpansion Configuration for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study_service.create_xpansion_configuration(
            uuid=uuid, zipped_config=file, params=params
        )

    @bp.delete(
        "/studies/{uuid}/extensions/xpansion",
        tags=[APITag.xpansion_study_management],
        summary="Delete Xpansion Configuration",
    )
    def delete_xpansion_configuration(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Deleting Xpansion Configuration for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study_service.delete_xpansion_configuration(uuid=uuid, params=params)

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/settings",
        tags=[APITag.xpansion_study_management],
        summary="Get Xpansion Settings",
        response_model=XpansionSettingsDTO,
    )
    def get_settings(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Fetching Xpansion Settings of the study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.get_xpansion_settings(uuid=uuid, params=params)

    @bp.put(
        "/studies/{uuid}/extensions/xpansion/settings",
        tags=[APITag.xpansion_study_management],
        summary="Update Xpansion Settings",
        response_model=XpansionSettingsDTO,
    )
    def update_settings(
        uuid: str,
        xpansion_settings_dto: XpansionSettingsDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Updating Xpansion Settings Of Study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.update_xpansion_settings(
            uuid, xpansion_settings_dto, params
        )

    @bp.put(
        "/studies/{uuid}/extensions/xpansion/settings/additional-constraints",
        tags=[APITag.xpansion_study_management],
        summary="Update Xpansion Settings Additional Constraints",
    )
    def update_additional_constraints_settings(
        uuid: str,
        filename: str = "",
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Updating Xpansion Settings Of Study {uuid} with additional constraints {filename}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study_service.update_xpansion_constraints_settings(
            uuid, filename, params
        )

    @bp.post(
        "/studies/{uuid}/extensions/xpansion/candidates",
        tags=[APITag.xpansion_study_management],
        summary="Create Xpansion Candidate",
    )
    def add_candidate(
        uuid: str,
        xpansion_candidate_dto: XpansionCandidateDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Adding new candidate {xpansion_candidate_dto.dict(by_alias=True)} to study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.add_candidate(
            uuid, xpansion_candidate_dto, params
        )

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/candidates/{candidate_name}",
        tags=[APITag.xpansion_study_management],
        summary="Get Xpansion Candidate",
        response_model=XpansionCandidateDTO,
    )
    def get_candidate(
        uuid: str,
        candidate_name: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(f"Fetching study list", extra={"user": current_user.id})
        params = RequestParameters(user=current_user)
        return study_service.get_candidate(uuid, candidate_name, params)

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/candidates",
        tags=[APITag.xpansion_study_management],
        summary="Get Xpansion Candidates",
        response_model=List[XpansionCandidateDTO],
    )
    def get_candidates(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(f"Fetching study list", extra={"user": current_user.id})
        params = RequestParameters(user=current_user)
        return study_service.get_candidates(uuid, params)

    @bp.put(
        "/studies/{uuid}/extensions/xpansion/candidates/{candidate_name}",
        tags=[APITag.xpansion_study_management],
        summary="Update Xpansion Candidate",
    )
    def update_candidate(
        uuid: str,
        candidate_name: str,
        xpansion_candidate_dto: XpansionCandidateDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Updating xpansion candidate {xpansion_candidate_dto.name} of the study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.update_xpansion_candidate(
            uuid, candidate_name, xpansion_candidate_dto, params
        )

    @bp.delete(
        "/studies/{uuid}/extensions/xpansion/candidates/{candidate_name}",
        tags=[APITag.xpansion_study_management],
        summary="Delete Xpansion Candidate",
    )
    def delete_candidate(
        uuid: str,
        candidate_name: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Deleting candidate {candidate_name} of the study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.delete_xpansion_candidate(
            uuid, candidate_name, params
        )

    @bp.post(
        "/studies/{uuid}/extensions/xpansion/resources/{resource_type}",
        tags=[APITag.xpansion_study_management],
        summary="Add Xpansion resource file",
    )
    def add_resource(
        uuid: str,
        resource_type: XpansionResourceFileType,
        file: UploadFile = File(...),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Add xpansion {resource_type} files in the study {uuid}",
            extra={"user": current_user.id},
        )
        study = study_service.check_study_access(
            uuid,
            StudyPermissionType.WRITE,
            RequestParameters(user=current_user),
        )
        return study_service.xpansion_manager.add_resource(
            study, resource_type, [file]
        )

    @bp.delete(
        "/studies/{uuid}/extensions/xpansion/resources/{resource_type}/{filename}",
        tags=[APITag.xpansion_study_management],
        summary="Delete Xpansion resource file",
    )
    def delete_resource(
        uuid: str,
        resource_type: XpansionResourceFileType,
        filename: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Deleting xpansion {resource_type} file from the study {uuid}",
            extra={"user": current_user.id},
        )
        study = study_service.check_study_access(
            uuid,
            StudyPermissionType.WRITE,
            RequestParameters(user=current_user),
        )
        return study_service.xpansion_manager.delete_resource(
            study, resource_type, filename
        )

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/resources/{resource_type}/{filename}",
        tags=[APITag.xpansion_study_management],
        summary="Getting Xpansion resource file content",
    )
    def get_resource_content(
        uuid: str,
        resource_type: XpansionResourceFileType,
        filename: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Getting xpansion {resource_type} file {filename} from the study {uuid}",
            extra={"user": current_user.id},
        )
        study = study_service.check_study_access(
            uuid,
            StudyPermissionType.READ,
            RequestParameters(user=current_user),
        )
        output: Union[
            JSON, bytes, str
        ] = study_service.xpansion_manager.get_resource_content(
            study, resource_type, filename
        )

        if isinstance(output, bytes):
            try:
                # try to decode string
                output = output.decode("utf-8")
            except (AttributeError, UnicodeDecodeError):
                pass

        json_response = json.dumps(
            output,
            ensure_ascii=False,
            allow_nan=True,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")
        return Response(content=json_response, media_type="application/json")

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/resources/{resource_type}",
        tags=[APITag.xpansion_study_management],
        summary="Getting all Xpansion resources files",
    )
    def list_resources(
        uuid: str,
        resource_type: Optional[XpansionResourceFileType] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Getting xpansion {resource_type} resources files from the study {uuid}",
            extra={"user": current_user.id},
        )
        study = study_service.check_study_access(
            uuid,
            StudyPermissionType.READ,
            RequestParameters(user=current_user),
        )
        if resource_type is None:
            return study_service.xpansion_manager.list_root_files(study)
        return study_service.xpansion_manager.list_resources(
            study, resource_type
        )

    return bp

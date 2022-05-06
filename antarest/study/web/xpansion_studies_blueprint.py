import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, UploadFile, File

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.requests import RequestParameters
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.study.business.xpansion_management import (
    XpansionSettingsDTO,
    XpansionCandidateDTO,
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
        filename: Optional[str] = None,
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
        "/studies/{uuid}/extensions/xpansion/constraints",
        tags=[APITag.xpansion_study_management],
        summary="Add Xpansion Constraints Files",
    )
    def add_constraints(
        uuid: str,
        file: UploadFile = File(...),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Add xpansion constraints files in the study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.add_xpansion_constraints(uuid, file, params)

    @bp.delete(
        "/studies/{uuid}/extensions/xpansion/constraints/{filename}",
        tags=[APITag.xpansion_study_management],
        summary="Delete Xpansion Constraints File",
    )
    def delete_constraints(
        uuid: str,
        filename: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Deleting xpansion constraints file from the study{uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.delete_xpansion_constraints(
            uuid, filename, params
        )

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/constraints/{filename}",
        tags=[APITag.xpansion_study_management],
        summary="Getting Xpansion Constraints File",
        response_model=bytes,
    )
    def get_constraints(
        uuid: str,
        filename: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Getting xpansion constraints file {filename} from the study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.get_single_xpansion_constraints(
            uuid, filename, params
        )

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/constraints",
        tags=[APITag.xpansion_study_management],
        summary="Getting all Xpansion Constraints Files",
    )
    def get_all_constraints(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Getting xpansion constraints file from the study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.get_all_xpansion_constraints(uuid, params)

    @bp.post(
        "/studies/{uuid}/extensions/xpansion/capacities",
        tags=[APITag.xpansion_study_management],
        summary="Adding New Capa Files",
    )
    def add_capa(
        uuid: str,
        file: UploadFile = File(...),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Adding new capa files to the study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.add_capa(uuid, file, params)

    @bp.delete(
        "/studies/{uuid}/extensions/xpansion/capacities/{filename}",
        tags=[APITag.xpansion_study_management],
        summary="Deleting Capa File",
    )
    def delete_capa(
        uuid: str,
        filename: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Deleting capa file {filename} from the study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.delete_capa(uuid, filename, params)

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/capacities/{filename}",
        tags=[APITag.xpansion_study_management],
        summary="Getting Capa File",
    )
    def get_single_capa(
        uuid: str,
        filename: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Getting capa file {filename} from the study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.get_single_capa(uuid, filename, params)

    @bp.get(
        "/studies/{uuid}/extensions/xpansion/capacities",
        tags=[APITag.xpansion_study_management],
        summary="Getting All Capa File",
    )
    def get_all_capa(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Getting all capacities files from the study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.get_all_capa(uuid, params)

    return bp

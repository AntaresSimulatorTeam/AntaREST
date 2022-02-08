import logging
from typing import Any

from fastapi import APIRouter, Depends

from antarest.core.config import Config
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.jwt import JWTUser
from antarest.core.requests import RequestParameters
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.study.business.xpansion_management import XpansionSettingsDTO
from antarest.study.service import StudyService

logger = logging.getLogger(__name__)


def create_study_routes(
    study_service: StudyService, ftm: FileTransferManager, config: Config
) -> APIRouter:
    """
    Endpoint implementation for xpansion studies management
    Args:
        study_service: study service facade to handle request
        ftm: file transfer manager
        config: main server configuration

    Returns:

    """
    bp = APIRouter(prefix="/v1/")
    auth = Auth(config)

    @bp.post(
        "/studies/{uuid}/extensions/xpansion/create",
        tags=[APITag.xpansion_study_management],
        summary="Create Xpansion Configuration",
    )
    def create_xpansion_configuration(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Creating Xpansion Configuration for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study_service.create_xpansion_configuration(uuid=uuid, params=params)

    @bp.post(
        "/studies/{uuid}/extensions/xpansion/delete",
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

    #
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

    #
    # @bp.post(
    #     "/studies/{uuid}/extensions/xpansion/settings",
    #     tags=[APITag.xpansion_study_management],
    #     summary="Update Xpansion Settings",
    #     response_model=Dict[str, StudyMetadataDTO],
    # )
    # def update_settings(
    #     summary: bool = False,
    #     managed: bool = False,
    #     current_user: JWTUser = Depends(auth.get_current_user),
    # ) -> Any:
    #     logger.info(f"Fetching study list", extra={"user": current_user.id})
    #     params = RequestParameters(user=current_user)
    #     available_studies = study_service.get_studies_information(
    #         summary, managed, params
    #     )
    #     return available_studies
    #
    # @bp.post(
    #     "/studies/{uuid}/extensions/xpansion/candidates/{candidate_id}/add",
    #     tags=[APITag.xpansion_study_management],
    #     summary="Create Xpansion Candidate",
    #     response_model=Dict[str, StudyMetadataDTO],
    # )
    # def add_candidate(
    #     summary: bool = False,
    #     managed: bool = False,
    #     current_user: JWTUser = Depends(auth.get_current_user),
    # ) -> Any:
    #     logger.info(f"Fetching study list", extra={"user": current_user.id})
    #     params = RequestParameters(user=current_user)
    #     available_studies = study_service.get_studies_information(
    #         summary, managed, params
    #     )
    #     return available_studies
    #
    # @bp.post(
    #     "/studies/{uuid}/extensions/xpansion/candidates/{candidate_id}/update",
    #     tags=[APITag.xpansion_study_management],
    #     summary="Update Xpansion Candidate",
    #     response_model=Dict[str, StudyMetadataDTO],
    # )
    # def update_candidate(
    #     summary: bool = False,
    #     managed: bool = False,
    #     current_user: JWTUser = Depends(auth.get_current_user),
    # ) -> Any:
    #     logger.info(f"Fetching study list", extra={"user": current_user.id})
    #     params = RequestParameters(user=current_user)
    #     available_studies = study_service.get_studies_information(
    #         summary, managed, params
    #     )
    #     return available_studies
    #
    # @bp.post(
    #     "/studies/{uuid}/extensions/xpansion/candidates/{candidate_id}/delete",
    #     tags=[APITag.xpansion_study_management],
    #     summary="Delete Xpansion Candidate",
    #     response_model=Dict[str, StudyMetadataDTO],
    # )
    # def delete_candidate(
    #     summary: bool = False,
    #     managed: bool = False,
    #     current_user: JWTUser = Depends(auth.get_current_user),
    # ) -> Any:
    #     logger.info(f"Fetching study list", extra={"user": current_user.id})
    #     params = RequestParameters(user=current_user)
    #     available_studies = study_service.get_studies_information(
    #         summary, managed, params
    #     )
    #     return available_studies
    #
    # @bp.post(
    #     "/studies/{uuid}/extensions/xpansion/constraints",
    #     tags=[APITag.xpansion_study_management],
    #     summary="Delete Xpansion Candidate",
    #     response_model=Dict[str, StudyMetadataDTO],
    # )
    # def update_constraints(
    #     summary: bool = False,
    #     managed: bool = False,
    #     current_user: JWTUser = Depends(auth.get_current_user),
    # ) -> Any:
    #     logger.info(f"Fetching study list", extra={"user": current_user.id})
    #     params = RequestParameters(user=current_user)
    #     available_studies = study_service.get_studies_information(
    #         summary, managed, params
    #     )
    #     return available_studies

    return bp

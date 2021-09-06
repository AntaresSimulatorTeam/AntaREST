import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.requests import (
    RequestParameters,
)
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.study.service import StudyService
from antarest.study.storage.area_management import (
    AreaType,
    AreaCreationDTO,
    AreaPatchUpdateDTO,
)

logger = logging.getLogger(__name__)


def create_study_area_routes(
    study_service: StudyService, config: Config
) -> APIRouter:
    """
    Endpoint implementation for studies area management
    Args:
        study_service: study service facade to handle request
        config: main server configuration

    Returns:

    """
    bp = APIRouter(prefix="/v1")
    auth = Auth(config)

    @bp.get(
        "/studies/{uuid}/areas",
        tags=[APITag.study_data],
        summary="Get all areas basic info",
    )
    def get_areas(
        uuid: str,
        type: Optional[AreaType] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Fetching area list (type={type}) for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        areas_list = study_service.get_all_areas(uuid, type, params)
        return areas_list

    @bp.post(
        "/studies/{uuid}/areas",
        tags=[APITag.study_data],
        summary="Create a new area/cluster",
    )
    def create_area(
        uuid: str,
        area_creation_info: AreaCreationDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Creating new area for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.create_area(uuid, area_creation_info, params)

    @bp.put(
        "/studies/{uuid}/areas/{area_id}",
        tags=[APITag.study_data],
        summary="Update area information",
    )
    def update_area_info(
        uuid: str,
        area_id: str,
        area_patch_dto: AreaPatchUpdateDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Updating area {area_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study_service.update_area(uuid, area_id, area_patch_dto, params)
        return ""

    @bp.delete(
        "/studies/{uuid}/areas/{area_id}",
        tags=[APITag.study_data],
        summary="Delete an area",
    )
    def delete_area(
        uuid: str,
        area_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Removing area {area_id} in study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study_service.delete_area(uuid, area_id, params)
        return area_id

    return bp

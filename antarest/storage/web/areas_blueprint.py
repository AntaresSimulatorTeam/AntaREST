import io
import json
from glob import escape
from http import HTTPStatus
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, File, Depends, Body
from fastapi.params import Param
from starlette.responses import StreamingResponse, Response

from antarest.common.config import Config
from antarest.common.custom_types import JSON
from antarest.common.jwt import JWTUser
from antarest.common.requests import (
    RequestParameters,
)
from antarest.common.swagger import get_path_examples
from antarest.common.utils.web import APITag
from antarest.login.auth import Auth
from antarest.storage.business.area_management import (
    AreaType,
    AreaCreationDTO,
    AreaPatchUpdateDTO,
)
from antarest.storage.service import StorageService


def create_study_area_routes(
    storage_service: StorageService, config: Config
) -> APIRouter:
    """
    Endpoint implementation for studies area management
    Args:
        storage_service: storage service facade to handle request
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
        params = RequestParameters(user=current_user)
        areas_list = storage_service.get_all_areas(uuid, type, params)
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
        params = RequestParameters(user=current_user)
        return storage_service.create_area(uuid, area_creation_info, params)

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
        params = RequestParameters(user=current_user)
        storage_service.update_area(uuid, area_id, area_patch_dto, params)
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
        params = RequestParameters(user=current_user)
        storage_service.delete_area(uuid, area_id, params)
        return area_id

    return bp

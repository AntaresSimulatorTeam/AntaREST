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
from antarest.storage.model import PublicMode, StudyMetadataPatchDTO
from antarest.storage.service import StorageService


def create_study_area_routes(
    storage_service: StorageService, config: Config
) -> APIRouter:
    """
    Endpoint implementation for studies management
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
        summary="Get Study informations",
    )
    def get_areas(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        params = RequestParameters(user=current_user)
        study_metadata = storage_service.get_study_information(uuid, params)
        return study_metadata

    @bp.post(
        "/studies/{uuid}/areas",
        tags=[APITag.study_data],
        summary="Get Study informations",
    )
    def create_area(
        uuid: str,
        study_metadata_patch: StudyMetadataPatchDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        params = RequestParameters(user=current_user)
        study_metadata = storage_service.update_study_information(
            uuid, study_metadata_patch, params
        )
        return study_metadata

    @bp.get(
        "/studies/{uuid}/areas/{area_id}",
        tags=[APITag.study_data],
        summary="Get Study informations",
    )
    def get_detail_area_info(uuid: str, area_id: str, current_user: JWTUser = Depends(auth.get_current_user)) -> Any:
        pass

    @bp.put(
        "/studies/{uuid}/areas/{area_id}",
        tags=[APITag.study_data],
        summary="Get Study informations",
    )
    def update_area_info(uuid: str, area_id: str, current_user: JWTUser = Depends(auth.get_current_user)) -> Any:
        pass

    @bp.delete(
        "/studies/{uuid}/areas/{area_id}",
        tags=[APITag.study_data],
        summary="Get Study informations",
    )
    def delete_area(uuid: str, area_id: str, current_user: JWTUser = Depends(auth.get_current_user)) -> Any:
        pass

    return bp

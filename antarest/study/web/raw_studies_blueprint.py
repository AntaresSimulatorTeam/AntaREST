import json
import logging
from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, HTTPException, File, Depends, Body
from fastapi.params import Param
from starlette.responses import Response

from antarest.core.custom_types import JSON
from antarest.core.jwt import JWTUser
from antarest.core.requests import (
    RequestParameters,
)
from antarest.core.swagger import get_path_examples
from antarest.core.utils.file_transfer import FileTransferManager
from antarest.core.utils.utils import sanitize_uuid
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.core.config import Config
from antarest.study.service import StudyService

logger = logging.getLogger(__name__)


def create_raw_study_routes(
    storage_service: StudyService, config: Config
) -> APIRouter:
    """
    Endpoint implementation for studies management
    Args:
        storage_service: study service facade to handle request
        config: main server configuration

    Returns:

    """
    bp = APIRouter(prefix="/v1")
    auth = Auth(config)

    @bp.get(
        "/studies/{uuid}/raw",
        tags=[APITag.study_raw_data],
        summary="Read data",
    )
    def get_study(
        uuid: str,
        path: str = Param("/", examples=get_path_examples()),  # type: ignore
        depth: int = 3,
        formatted: bool = True,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Fetching data at {path} (depth={depth}) from study {uuid}",
            extra={"user": current_user.id},
        )
        parameters = RequestParameters(user=current_user)
        output = storage_service.get(uuid, path, depth, formatted, parameters)

        try:
            # try to decode string
            output = output.decode("utf-8")  # type: ignore
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

    @bp.post(
        "/studies/{uuid}/raw",
        status_code=HTTPStatus.NO_CONTENT.value,
        tags=[APITag.study_raw_data],
        summary="Update data by posting formatted data",
    )
    def edit_study(
        uuid: str,
        path: str = Param("/", examples=get_path_examples()),  # type: ignore
        data: JSON = Body(...),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Editing data at {path} for study {uuid}",
            extra={"user": current_user.id},
        )
        new = data
        if not new:
            raise HTTPException(
                status_code=400, detail="empty body not authorized"
            )

        path = sanitize_uuid(path)
        params = RequestParameters(user=current_user)
        storage_service.edit_study(uuid, path, new, params)
        content = ""

        return content

    @bp.put(
        "/studies/{uuid}/raw",
        status_code=HTTPStatus.NO_CONTENT.value,
        tags=[APITag.study_raw_data],
        summary="Update data by posting a raw file",
    )
    def replace_study_file(
        uuid: str,
        path: str = Param("/", examples=get_path_examples()),  # type: ignore
        file: bytes = File(...),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Uploading new data file at {path} for study {uuid}",
            extra={"user": current_user.id},
        )
        path = sanitize_uuid(path)
        params = RequestParameters(user=current_user)
        storage_service.edit_study(uuid, path, file, params)
        content = ""

        return content

    @bp.get(
        "/studies/{uuid}/raw/validate",
        summary="Launch test validation on study",
        tags=[APITag.study_raw_data],
    )
    def validate(
        uuid: str, current_user: JWTUser = Depends(auth.get_current_user)
    ) -> Any:
        logger.info(
            f"Validating data for study {uuid}",
            extra={"user": current_user.id},
        )
        return storage_service.check_errors(uuid)

    return bp

import logging
from typing import Any, Optional, List

from fastapi import APIRouter, Depends

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.requests import (
    RequestParameters,
)
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.study.model import StudyMetadataDTO
from antarest.study.service import StudyService
from antarest.study.storage.variantstudy.model import (
    GenerationResultInfoDTO,
    CommandDTO,
)

logger = logging.getLogger(__name__)


def create_study_variant_routes(
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

    @bp.post(
        "/studies/{uuid}/variants",
        tags=[APITag.study_variant_management],
        summary="Create a study variant",
        responses={
            200: {
                "description": "The id of the new study variant",
            }
        },
    )
    def create_variant(
        uuid: str,
        name: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> str:
        logger.info(
            f"Creating new variant '{name}' from study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        raise NotImplementedError()

    @bp.get(
        "/studies/{uuid}/variants",
        tags=[APITag.study_variant_management],
        summary="Get children variants",
        responses={
            200: {
                "description": "The list of children study variant",
                "model": List[StudyMetadataDTO],
            }
        },
    )
    def get_variants(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> List[StudyMetadataDTO]:
        logger.info(
            f"Fetching variant children of study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        raise NotImplementedError()

    @bp.get(
        "/studies/{uuid}/commands",
        tags=[APITag.study_variant_management],
        summary="List variant commands",
        responses={
            200: {
                "description": "The detail of a command content",
                "model": List[CommandDTO],
            }
        },
    )
    def list_commands(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> List[CommandDTO]:
        logger.info(
            f"Fetching command list of variant study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        raise NotImplementedError()

    @bp.post(
        "/studies/{uuid}/commands",
        tags=[APITag.study_variant_management],
        summary="Append a command to variant",
        responses={
            200: {
                "description": "The id a the appended command",
            }
        },
    )
    def append_command(
        uuid: str,
        command: List[CommandDTO],
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> str:
        logger.info(
            f"Appending new command to variant study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        raise NotImplementedError()

    @bp.get(
        "/studies/{uuid}/commands/{cid}",
        tags=[APITag.study_variant_management],
        summary="Get a command detail",
        responses={
            200: {
                "description": "The detail of a command content",
            }
        },
    )
    def get_command(
        uuid: str,
        cid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> CommandDTO:
        logger.info(
            f"Fetching command {cid} info of variant study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        raise NotImplementedError()

    @bp.put(
        "/studies/{uuid}/commands/{cid}",
        tags=[APITag.study_variant_management],
        summary="Move a command to an other index",
    )
    def move_command(
        uuid: str,
        cid: str,
        index: int,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            f"Moving command {cid} to index {index} for variant study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        raise NotImplementedError()

    @bp.delete(
        "/studies/{uuid}/commands/{cid}",
        tags=[APITag.study_variant_management],
        summary="Remove a command",
    )
    def remove_command(
        uuid: str,
        cid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            f"Removing command {cid} of variant study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        raise NotImplementedError()

    @bp.put(
        "/studies/{uuid}/generate",
        tags=[APITag.study_variant_management],
        summary="Generate variant snapshot",
        responses={
            200: {
                "description": "The result of the generation process",
                "model": GenerationResultInfoDTO,
            }
        },
    )
    def generate_variant(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> GenerationResultInfoDTO:
        logger.info(
            f"Generating snapshot for variant study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        raise NotImplementedError()

    @bp.post(
        "/studies/{uuid}/freeze",
        tags=[APITag.study_variant_management],
        summary="Generate a new raw study",
        responses={
            200: {
                "description": "The id of the new study",
            }
        },
    )
    def create_from_variant(
        uuid: str,
        name: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> str:
        logger.info(
            f"Creating new raw study {name} from variant study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        raise NotImplementedError()

    return bp

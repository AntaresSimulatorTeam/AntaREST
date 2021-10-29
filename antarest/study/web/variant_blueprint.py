import logging
from typing import List, Dict, Union

from fastapi import APIRouter, Depends, Body

from antarest.core.config import Config
from antarest.core.custom_types import JSON
from antarest.core.jwt import JWTUser
from antarest.core.requests import (
    RequestParameters,
)
from antarest.core.tasks.model import TaskDTO
from antarest.core.utils.utils import sanitize_uuid
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.study.model import StudyMetadataDTO
from antarest.study.service import StudyService
from antarest.study.storage.variantstudy.model.model import (
    GenerationResultInfoDTO,
    CommandDTO,
    VariantTreeDTO,
)
from antarest.study.storage.variantstudy.variant_study_service import (
    VariantStudyService,
)

logger = logging.getLogger(__name__)


def create_study_variant_routes(
    variant_study_service: VariantStudyService,
    config: Config,
) -> APIRouter:
    """
    Endpoint implementation for studies area management
    Args:
        variant_study_service: study service facade to handle request
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
        sanitized_uuid = sanitize_uuid(uuid)
        params = RequestParameters(user=current_user)
        logger.info(
            f"Creating new variant '{name}' from study {uuid}",
            extra={"user": current_user.id},
        )

        output = variant_study_service.create_variant_study(
            uuid=sanitized_uuid, name=name, params=params
        )
        return output or ""

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
    ) -> VariantTreeDTO:
        logger.info(
            f"Fetching variant children of study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        sanitized_uuid = sanitize_uuid(uuid)
        return variant_study_service.get_all_variants_children(
            sanitized_uuid, params
        )

    @bp.get(
        "/studies/{uuid}/parents",
        tags=[APITag.study_variant_management],
        summary="Get parents of variant",
        responses={
            200: {
                "description": "The list of children study variant",
                "model": List[StudyMetadataDTO],
            }
        },
    )
    def get_parents(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> List[StudyMetadataDTO]:
        logger.info(
            f"Fetching variant parents of study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        sanitized_uuid = sanitize_uuid(uuid)
        return variant_study_service.get_variants_parents(
            sanitized_uuid, params
        )

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
        sanitized_uuid = sanitize_uuid(uuid)
        return variant_study_service.get_commands(sanitized_uuid, params)

    @bp.post(
        "/studies/{uuid}/commands",
        tags=[APITag.study_variant_management],
        summary="Append a command to variant",
        responses={
            200: {
                "description": "The id of the study",
            }
        },
    )
    def append_commands(
        uuid: str,
        commands: List[CommandDTO] = Body(...),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> str:
        logger.info(
            f"Appending new command to variant study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        sanitized_uuid = sanitize_uuid(uuid)
        return variant_study_service.append_commands(
            sanitized_uuid, commands, params
        )

    @bp.put(
        "/studies/{uuid}/commands",
        tags=[APITag.study_variant_management],
        summary="Replace all commands from variant",
        responses={
            200: {
                "description": "The id of the study",
            }
        },
    )
    def replace_commands(
        uuid: str,
        commands: List[CommandDTO] = Body(...),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> str:
        logger.info(
            f"Replacing all commands of variant study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        sanitized_uuid = sanitize_uuid(uuid)
        return variant_study_service.replace_commands(
            sanitized_uuid, commands, params
        )

    @bp.post(
        "/studies/{uuid}/command",
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
        command: CommandDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> str:
        logger.info(
            f"Appending new command to variant study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        sanitized_uuid = sanitize_uuid(uuid)
        return variant_study_service.append_command(
            sanitized_uuid, command, params
        )

    @bp.get(
        "/studies/{uuid}/commands/{cid}",
        tags=[APITag.study_variant_management],
        summary="Get a command detail",
        responses={
            200: {
                "description": "The detail of a command content",
                "model": CommandDTO,
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
        sanitized_uuid = sanitize_uuid(uuid)
        sanitized_cid = sanitize_uuid(cid)
        return variant_study_service.get_command(
            sanitized_uuid, sanitized_cid, params
        )

    @bp.put(
        "/studies/{uuid}/commands/{cid}/move",
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
        sanitized_uuid = sanitize_uuid(uuid)
        sanitized_cid = sanitize_uuid(cid)
        variant_study_service.move_command(
            sanitized_uuid, sanitized_cid, index, params
        )

    @bp.put(
        "/studies/{uuid}/commands/{cid}",
        tags=[APITag.study_variant_management],
        summary="Move a command to an other index",
    )
    def update_command(
        uuid: str,
        cid: str,
        command: CommandDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            f"Update command {cid} for variant study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        sanitized_uuid = sanitize_uuid(uuid)
        sanitized_cid = sanitize_uuid(cid)
        variant_study_service.update_command(
            sanitized_uuid, sanitized_cid, command, params
        )

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
        sanitized_uuid = sanitize_uuid(uuid)
        sanitized_cid = sanitize_uuid(cid)
        variant_study_service.remove_command(
            sanitized_uuid, sanitized_cid, params
        )

    @bp.delete(
        "/studies/{uuid}/commands",
        tags=[APITag.study_variant_management],
        summary="Clear variant's commands",
    )
    def remove_all_commands(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(
            f"Removing all commands from variant study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        sanitized_uuid = sanitize_uuid(uuid)
        variant_study_service.remove_all_commands(sanitized_uuid, params)

    @bp.put(
        "/studies/{uuid}/generate",
        tags=[APITag.study_variant_management],
        summary="Generate variant snapshot",
        response_model=str,
    )
    def generate_variant(
        uuid: str,
        denormalize: bool = False,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> str:
        logger.info(
            f"Generating snapshot for variant study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        sanitized_uuid = sanitize_uuid(uuid)
        return variant_study_service.generate(
            sanitized_uuid, denormalize, params
        )

    @bp.get(
        "/studies/{uuid}/task",
        tags=[APITag.study_variant_management],
        summary="Get study generation task",
        response_model=TaskDTO,
    )
    def get_study_generation_task(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> TaskDTO:
        request_params = RequestParameters(user=current_user)
        sanitized_uuid = sanitize_uuid(uuid)
        return variant_study_service.get_study_task(
            sanitized_uuid, request_params
        )

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

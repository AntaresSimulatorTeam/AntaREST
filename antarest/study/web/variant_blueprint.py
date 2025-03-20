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
import datetime
import logging
from typing import List, Optional, Union

import humanize
from fastapi import APIRouter, Body, Depends

from antarest.core.config import Config
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.jwt import JWTUser
from antarest.core.requests import RequestParameters
from antarest.core.tasks.model import TaskDTO
from antarest.core.utils.utils import sanitize_string, sanitize_uuid
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.study.model import StudyMetadataDTO
from antarest.study.service import StudyService
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.model import CommandDTOAPI, VariantTreeDTO

logger = logging.getLogger(__name__)


def create_study_variant_routes(
    study_service: StudyService,
    config: Config,
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
    variant_study_service = study_service.storage_service.variant_study_service

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
        """
        Creates a study variant.

        Parameters:
        - `uuid`: The UUID of the parent study.
        - `name`: The name of the new study variant.
        """
        sanitized_uuid = sanitize_uuid(uuid)
        params = RequestParameters(user=current_user)
        logger.info(f"Creating new variant '{name}' from study {uuid}")
        variant_study = variant_study_service.create_variant_study(uuid=sanitized_uuid, name=name, params=params)

        author = study_service.get_user_name(params)
        parent_author = variant_study.additional_data.author
        if author != parent_author:
            command_context = study_service.storage_service.variant_study_service.command_factory.command_context
            study_service.apply_commands(
                variant_study.id,
                [
                    UpdateConfig(
                        target="study",
                        data={
                            "antares": {
                                "version": variant_study.version,
                                "caption": variant_study.name,
                                "created": variant_study.created_at.timestamp(),
                                "lastsave": variant_study.created_at.timestamp(),
                                "author": author,
                            }
                        },
                        command_context=command_context,
                        study_version=variant_study.version,
                    ).to_dto()
                ],
                params,
            )
        return str(variant_study.id)

    @bp.get(
        "/studies/{uuid}/variants",
        tags=[APITag.study_variant_management],
        summary="Get children variants",
        response_model=None,  # To cope with recursive models issues
    )
    def get_variants(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> VariantTreeDTO:
        logger.info(f"Fetching variant children of study {uuid}")
        params = RequestParameters(user=current_user)
        sanitized_uuid = sanitize_uuid(uuid)
        return variant_study_service.get_all_variants_children(sanitized_uuid, params)

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
        direct: Optional[bool] = False,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Union[List[StudyMetadataDTO], Optional[StudyMetadataDTO]]:
        logger.info(f"Fetching variant parents of study {uuid}")
        params = RequestParameters(user=current_user)
        sanitized_uuid = sanitize_uuid(uuid)
        return (
            variant_study_service.get_variants_parents(sanitized_uuid, params)
            if not direct
            else variant_study_service.get_direct_parent(sanitized_uuid, params)
        )

    @bp.get(
        "/studies/{uuid}/commands",
        tags=[APITag.study_variant_management],
        summary="List variant commands",
        responses={
            200: {
                "description": "The detail of a command content",
                "model": List[CommandDTOAPI],
            }
        },
    )
    def list_commands(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> List[CommandDTOAPI]:
        """
        Get the list of commands of a variant.

        Parameters:
        - `uuid`: the study id

        Returns:
        - The list of variant commands
        """
        logger.info(f"Fetching command list of variant study {uuid}")
        params = RequestParameters(user=current_user)
        sanitized_uuid = sanitize_uuid(uuid)
        return variant_study_service.get_commands(sanitized_uuid, params)

    @bp.get(
        "/studies/{uuid}/commands/_matrices",
        tags=[APITag.study_variant_management],
        summary="Export a variant's commands matrices",
        response_model=FileDownloadTaskDTO,
    )
    def export_matrices(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> FileDownloadTaskDTO:
        logger.info(f"Exporting commands matrices for variant study {uuid}")
        params = RequestParameters(user=current_user)
        sanitized_uuid = sanitize_uuid(uuid)
        return variant_study_service.export_commands_matrices(sanitized_uuid, params)

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
        commands: List[CommandDTOAPI] = Body(...),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Optional[List[str]]:
        """
        Append a list of commands to a variant study.

        Parameters:
        - `uuid`: the study id
        - `commands`: the list of commands

        Returns:
        - The list of the newly appended commands if the study is a variant, None otherwise.
        """
        logger.info(f"Appending new command to variant study {uuid}")
        params = RequestParameters(user=current_user)
        sanitized_uuid = sanitize_uuid(uuid)
        internal_commands = variant_study_service.convert_commands(sanitized_uuid, commands, params)
        return study_service.apply_commands(sanitized_uuid, internal_commands, params)

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
        commands: List[CommandDTOAPI] = Body(...),
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> str:
        logger.info(f"Replacing all commands of variant study {uuid}")
        params = RequestParameters(user=current_user)
        sanitized_uuid = sanitize_uuid(uuid)
        internal_commands = variant_study_service.convert_commands(sanitized_uuid, commands, params)
        return variant_study_service.replace_commands(sanitized_uuid, internal_commands, params)

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
        command: CommandDTOAPI,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> str:
        logger.info(f"Appending new command to variant study {uuid}")
        params = RequestParameters(user=current_user)
        sanitized_uuid = sanitize_uuid(uuid)
        internal_command = variant_study_service.convert_commands(sanitized_uuid, [command], params)[0]
        return variant_study_service.append_command(sanitized_uuid, internal_command, params)

    @bp.get(
        "/studies/{uuid}/commands/{cid}",
        tags=[APITag.study_variant_management],
        summary="Get a command detail",
        responses={
            200: {
                "description": "The detail of a command content",
                "model": CommandDTOAPI,
            }
        },
    )
    def get_command(
        uuid: str,
        cid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> CommandDTOAPI:
        logger.info(f"Fetching command {cid} info of variant study {uuid}")
        params = RequestParameters(user=current_user)
        sanitized_uuid = sanitize_uuid(uuid)
        sanitized_cid = sanitize_string(cid)
        return variant_study_service.get_command(sanitized_uuid, sanitized_cid, params)

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
        logger.info(f"Moving command {cid} to index {index} for variant study {uuid}")
        params = RequestParameters(user=current_user)
        sanitized_uuid = sanitize_uuid(uuid)
        sanitized_cid = sanitize_string(cid)
        variant_study_service.move_command(sanitized_uuid, sanitized_cid, index, params)

    @bp.put(
        "/studies/{uuid}/commands/{cid}",
        tags=[APITag.study_variant_management],
        summary="Move a command to an other index",
    )
    def update_command(
        uuid: str,
        cid: str,
        command: CommandDTOAPI,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(f"Update command {cid} for variant study {uuid}")
        params = RequestParameters(user=current_user)
        sanitized_uuid = sanitize_uuid(uuid)
        sanitized_cid = sanitize_string(cid)
        internal_command = variant_study_service.convert_commands(sanitized_uuid, [command], params)[0]
        variant_study_service.update_command(sanitized_uuid, sanitized_cid, internal_command, params)

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
        logger.info(f"Removing command {cid} of variant study {uuid}")
        params = RequestParameters(user=current_user)
        sanitized_uuid = sanitize_uuid(uuid)
        sanitized_cid = sanitize_string(cid)
        variant_study_service.remove_command(sanitized_uuid, sanitized_cid, params)

    @bp.delete(
        "/studies/{uuid}/commands",
        tags=[APITag.study_variant_management],
        summary="Clear variant's commands",
    )
    def remove_all_commands(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> None:
        logger.info(f"Removing all commands from variant study {uuid}")
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
        from_scratch: bool = False,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> str:
        logger.info(f"Generating snapshot for variant study {uuid}")
        params = RequestParameters(user=current_user)
        sanitized_uuid = sanitize_uuid(uuid)
        return variant_study_service.generate(sanitized_uuid, denormalize, from_scratch, params)

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
        return variant_study_service.get_study_task(sanitized_uuid, request_params)

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
        logger.info(f"Creating new raw study {name} from variant study {uuid}")
        raise NotImplementedError()

    @bp.put(
        "/studies/variants/clear-snapshots",
        tags=[APITag.study_variant_management],
        summary="Clear variant snapshots",
        responses={
            200: {
                "description": "Delete snapshots older than a specific number of hours. By default, this number is 24."
            }
        },
    )
    def clear_variant_snapshots(
        hours: int = 24,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> str:
        """
        Endpoint that clear snapshots of variant which were updated or accessed `hours` hours ago.

        Args: hours (int, optional): Number of hours to clear. Defaults to 24.

        Returns: ID of the task running the snapshot clearing.
        """
        retention_hours = datetime.timedelta(hours=hours)
        logger.info(f"Delete all variant snapshots older than {humanize.precisedelta(retention_hours)}.")
        params = RequestParameters(user=current_user)
        return variant_study_service.clear_all_snapshots(retention_hours, params)

    return bp

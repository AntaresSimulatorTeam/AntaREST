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

import collections
import io
import logging
from http import HTTPStatus
from pathlib import PurePosixPath
from typing import Annotated, Any, Dict, List, Optional, Sequence

from fastapi import APIRouter, File, HTTPException, Query
from markupsafe import escape
from pydantic import NonNegativeInt

from antarest.core.config import Config
from antarest.core.exceptions import BadArchiveContent, BadZipBinary
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.model import PublicMode
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.utils.utils import sanitize_string, sanitize_uuid
from antarest.core.utils.web import APITag
from antarest.login.utils import get_current_user
from antarest.study.model import (
    CommentsDto,
    MatrixIndex,
    StudyMetadataDTO,
    StudyMetadataPatchDTO,
    StudyVersionStr,
)
from antarest.study.repository import AccessPermissions, StudyFilter, StudyPagination, StudySortBy
from antarest.study.service import StudyService
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfigDTO

logger = logging.getLogger(__name__)

QUERY_REGEX = r"^\s*(?:\d+\s*(?:,\s*\d+\s*)*)?$"


def _split_comma_separated_values(value: str, *, default: Sequence[str] = ()) -> Sequence[str]:
    """Split a comma-separated list of values into an ordered set of strings."""
    values = value.split(",") if value else default
    # drop whitespace around values
    values = [v.strip() for v in values]
    # remove duplicates and preserve order (to have a deterministic result for unit tests).
    return list(collections.OrderedDict.fromkeys(values))


def create_study_routes(study_service: StudyService, ftm: FileTransferManager, config: Config) -> APIRouter:
    """
    Endpoint implementation for studies management
    Args:
        study_service: study service facade to handle request
        ftm: file transfer manager
        config: main server configuration

    Returns:

    """
    bp = APIRouter(prefix="/v1")

    @bp.get(
        "/studies",
        tags=[APITag.study_management],
        summary="Get Studies",
    )
    def get_studies(
        name: str = Query(
            "",
            description=(
                "Filter studies based on their name."
                "Case-insensitive search for studies whose name contains the specified value."
            ),
            alias="name",
        ),
        managed: Optional[bool] = Query(None, description="Filter studies based on their management status."),
        archived: Optional[bool] = Query(None, description="Filter studies based on their archive status."),
        variant: Optional[bool] = Query(None, description="Filter studies based on their variant status."),
        versions: str = Query("", description="Comma-separated list of versions for filtering.", regex=QUERY_REGEX),
        users: str = Query("", description="Comma-separated list of user IDs for filtering.", regex=QUERY_REGEX),
        groups: str = Query("", description="Comma-separated list of group IDs for filtering."),
        tags: str = Query("", description="Comma-separated list of tags for filtering."),
        study_ids: str = Query("", description="Comma-separated list of study IDs for filtering.", alias="studyIds"),
        exists: Optional[bool] = Query(None, description="Filter studies based on their existence on disk."),
        workspace: str = Query("", description="Filter studies based on their workspace."),
        folder: str = Query("", description="Filter studies based on their folder."),
        sort_by: StudySortBy = Query(
            None,
            description="Sort studies based on their name (case-insensitive) or creation date.",
            alias="sortBy",
        ),
        page_nb: NonNegativeInt = Query(0, description="Page number (starting from 0).", alias="pageNb"),
        page_size: NonNegativeInt = Query(
            0, description="Number of studies per page (0 = no limit).", alias="pageSize"
        ),
    ) -> Dict[str, StudyMetadataDTO]:
        """
        Get the list of studies matching the specified criteria.

        Args:

        - `name`: Filter studies based on their name. Case-insensitive search for studies
        - `managed`: Filter studies based on their management status.
        - `archived`: Filter studies based on their archive status.
        - `variant`: Filter studies based on their variant status.
        - `versions`: Comma-separated list of versions for filtering.
        - `users`: Comma-separated list of user IDs for filtering.
        - `groups`: Comma-separated list of group IDs for filtering.
        - `tags`: Comma-separated list of tags for filtering.
        - `studyIds`: Comma-separated list of study IDs for filtering.
        - `exists`: Filter studies based on their existence on disk.
        - `workspace`: Filter studies based on their workspace.
        - `folder`: Filter studies based on their folder.
        - `sortBy`: Sort studies based on their name (case-insensitive) or date.
        - `pageNb`: Page number (starting from 0).
        - `pageSize`: Number of studies per page (0 = no limit).

        Returns:
        - A dictionary of studies matching the specified criteria,
          where keys are study IDs and values are study properties.
        """

        logger.info("Fetching for matching studies")

        user_list = [int(v) for v in _split_comma_separated_values(users)]

        user = get_current_user()
        if not user:
            raise UserHasNotPermissionError("FAIL permission: user is not logged")

        study_filter = StudyFilter(
            name=name,
            managed=managed,
            archived=archived,
            variant=variant,
            versions=_split_comma_separated_values(versions),
            users=user_list,
            groups=_split_comma_separated_values(groups),
            tags=_split_comma_separated_values(tags),
            study_ids=_split_comma_separated_values(study_ids),
            exists=exists,
            workspace=workspace,
            folder=folder,
            access_permissions=AccessPermissions.from_params(user),
        )

        matching_studies = study_service.get_studies_information(
            study_filter=study_filter,
            sort_by=sort_by,
            pagination=StudyPagination(page_nb=page_nb, page_size=page_size),
        )

        return matching_studies

    @bp.get(
        "/studies/count",
        tags=[APITag.study_management],
        summary="Count Studies",
    )
    def count_studies(
        name: str = Query("", description="Case-insensitive: filter studies based on their name.", alias="name"),
        managed: Optional[bool] = Query(None, description="Management status filter."),
        archived: Optional[bool] = Query(None, description="Archive status filter."),
        variant: Optional[bool] = Query(None, description="Variant status filter."),
        versions: str = Query("", description="Comma-separated versions filter.", regex=QUERY_REGEX),
        users: str = Query("", description="Comma-separated user IDs filter.", regex=QUERY_REGEX),
        groups: str = Query("", description="Comma-separated group IDs filter."),
        tags: str = Query("", description="Comma-separated tags filter."),
        study_ids: str = Query("", description="Comma-separated study IDs filter.", alias="studyIds"),
        exists: Optional[bool] = Query(None, description="Existence on disk filter."),
        workspace: str = Query("", description="Workspace filter."),
        folder: str = Query("", description="Study folder filter."),
    ) -> int:
        """
        Get the number of studies matching the specified criteria.

        Args:

        - `name`: Regexp to filter through studies based on their names
        - `managed`: Whether to limit the selection based on management status.
        - `archived`: Whether to limit the selection based on archive status.
        - `variant`: Whether to limit the selection either raw or variant studies.
        - `versions`: Comma-separated versions for studies to be selected.
        - `users`: Comma-separated user IDs for studies to be selected.
        - `groups`: Comma-separated group IDs for studies to be selected.
        - `tags`: Comma-separated tags for studies to be selected.
        - `studyIds`: Comma-separated IDs of studies to be selected.
        - `exists`: Whether to limit the selection based on studies' existence on disk.
        - `workspace`: to limit studies selection based on their workspace.
        - `folder`: to limit studies selection based on their folder.

        Returns:
        - An integer representing the total number of studies matching the filters above and the user permissions.
        """

        logger.info("Counting matching studies")
        user_list = [int(v) for v in _split_comma_separated_values(users)]

        user = get_current_user()
        if not user:
            raise UserHasNotPermissionError("FAIL permission: user is not logged")

        count = study_service.count_studies(
            study_filter=StudyFilter(
                name=name,
                managed=managed,
                archived=archived,
                variant=variant,
                versions=_split_comma_separated_values(versions),
                users=user_list,
                groups=_split_comma_separated_values(groups),
                tags=_split_comma_separated_values(tags),
                study_ids=_split_comma_separated_values(study_ids),
                exists=exists,
                workspace=workspace,
                folder=folder,
                access_permissions=AccessPermissions.from_params(user),
            ),
        )

        return count

    @bp.get(
        "/studies/{uuid}/comments",
        tags=[APITag.study_management],
        summary="Get comments",
    )
    def get_comments(uuid: str) -> Any:
        logger.info(f"Get comments of study {uuid}")
        study_id = sanitize_uuid(uuid)
        return study_service.get_comments(study_id)

    @bp.put(
        "/studies/{uuid}/comments",
        status_code=HTTPStatus.NO_CONTENT,
        tags=[APITag.study_raw_data],
        summary="Update comments",
        response_model=None,
    )
    def edit_comments(uuid: str, data: CommentsDto) -> Any:
        logger.info(f"Editing comments for study {uuid}")
        new = data
        if not new:
            raise HTTPException(status_code=400, detail="empty body not authorized")
        study_id = sanitize_uuid(uuid)
        study_service.edit_comments(study_id, new)

    @bp.post(
        "/studies/_import",
        status_code=HTTPStatus.CREATED,
        tags=[APITag.study_management],
        summary="Import Study",
        response_model=str,
    )
    def import_study(study: bytes = File(...), groups: str = "") -> str:
        """
        Upload and import a compressed study from your computer to the Antares Web server.

        Args:
        - `study`: The binary content of the study file in ZIP or 7z format.
        - `groups`: The groups your study will belong to (Default: current user's groups).

        Returns:
        - The ID of the imported study.

        Raises:
        - 415 error if the archive is corrupted or in an unknown format.
        """
        logger.info("Importing new study")
        zip_binary = io.BytesIO(study)

        user = get_current_user()
        group_ids: list[str] = []
        if user:
            group_ids_raw = _split_comma_separated_values(groups, default=[group.id for group in user.groups])
            group_ids = [sanitize_string(gid) for gid in group_ids_raw]

        try:
            uuid = study_service.import_study(zip_binary, group_ids)
        except BadArchiveContent as e:
            raise BadZipBinary(str(e))

        return uuid

    @bp.put(
        "/studies/{uuid}/upgrade",
        status_code=HTTPStatus.OK,
        tags=[APITag.study_management],
        summary="Upgrade study to the target version (or next version if not specified)",
    )
    def upgrade_study(uuid: str, target_version: str = "") -> str:
        """
        Upgrade a study to the target version or the next version if the target
        version is not specified.

        This method starts an upgrade task in the task manager.

        Args:
        - `uuid`: UUID of the study to upgrade.
        - `target_version`: target study version, or "" to upgrade to the next version.

        Returns:
        - The unique identifier of the task upgrading the study.
        """
        msg = (
            f"Upgrade study {uuid} to the version {target_version}"
            if target_version
            else f"Upgrade study {uuid} to the next version"
        )
        logger.info(msg)
        # returns the task ID
        return study_service.upgrade_study(uuid, target_version)

    @bp.post(
        "/studies/{uuid}/copy",
        status_code=HTTPStatus.CREATED,
        tags=[APITag.study_management],
        summary="Copy Study",
        response_model=str,
    )
    def copy_study(
        uuid: str,
        dest: str,
        output_ids: Annotated[list[str], Query(default_factory=list)],
        with_outputs: bool | None = None,
        groups: str = "",
        use_task: bool = True,
        destination_folder: str = "",
    ) -> str:
        """
        This endpoint enables you to duplicate a study and place it in a specified location.
        You can, for instance, copy a non-managed study to a managed workspace.

        Args:
        - `uuid`: The identifier of the study you wish to duplicate.
        - `dest`: The destination workspace where the study will be copied.
        - `with_outputs`: Indicates whether the study's outputs should also be duplicated.
        - `groups`: Specifies the groups to which your duplicated study will be assigned.
        - `use_task`: Determines whether this duplication operation should trigger a task.
            It is recommended and set as the default value: True.
        - `destination_folder`: The destination path where the study will be copied.
        - `output_ids`: A list of output names that you want to include in the destination study.

        Returns:
        - The unique identifier of the task copying the study.
        """
        logger.info(f"Copying study {uuid} into new study '{dest}'")

        user = get_current_user()
        group_ids: list[str] = []
        if user:
            group_ids_raw = _split_comma_separated_values(groups, default=[group.id for group in user.groups])
            group_ids = [sanitize_string(gid) for gid in group_ids_raw]

        uuid_sanitized = sanitize_uuid(uuid)
        destination_name_sanitized = escape(dest)

        task_id = study_service.copy_study(
            src_uuid=uuid_sanitized,
            dest_study_name=destination_name_sanitized,
            group_ids=group_ids,
            with_outputs=with_outputs,
            use_task=use_task,
            destination_folder=PurePosixPath(destination_folder),
            output_ids=output_ids,
        )

        return task_id

    @bp.put(
        "/studies/{uuid}/move",
        tags=[APITag.study_management],
        summary="Move study",
    )
    def move_study(uuid: str, folder_dest: str) -> Any:
        logger.info(f"Moving study {uuid} into folder '{folder_dest}'")
        study_service.move_study(uuid, folder_dest)

    @bp.post(
        "/studies",
        status_code=HTTPStatus.CREATED,
        tags=[APITag.study_management],
        summary="Create a new empty study",
        response_model=str,
    )
    def create_study(name: str, version: StudyVersionStr | None = None, groups: str = "") -> Any:
        logger.info(f"Creating new study '{name}'")
        name_sanitized = escape(name)
        group_ids = _split_comma_separated_values(groups)
        group_ids = [sanitize_string(gid) for gid in group_ids]

        uuid = study_service.create_study(name_sanitized, version, group_ids)

        return uuid

    @bp.get(
        "/studies/{uuid}/synthesis",
        tags=[APITag.study_management],
        summary="Return study synthesis",
        response_model=FileStudyTreeConfigDTO,
    )
    def get_study_synthesis(uuid: str) -> Any:
        study_id = sanitize_uuid(uuid)
        logger.info(f"Return a synthesis for study '{study_id}'")
        return study_service.get_study_synthesis(study_id)

    @bp.get(
        "/studies/{uuid}/matrixindex",
        tags=[APITag.study_management],
        summary="Return study input matrix start date index",
        response_model=MatrixIndex,
    )
    def get_study_matrix_index(uuid: str, path: str = "") -> Any:
        study_id = sanitize_uuid(uuid)
        logger.info(f"Return the start date for input matrix '{study_id}'")
        return study_service.get_input_matrix_startdate(study_id, path)

    @bp.get(
        "/studies/{uuid}/export",
        tags=[APITag.study_management],
        summary="Export Study",
        response_model=FileDownloadTaskDTO,
    )
    def export_study(uuid: str, no_output: Optional[bool] = False) -> Any:
        logger.info(f"Exporting study {uuid}")
        uuid_sanitized = sanitize_uuid(uuid)

        return study_service.export_study(uuid_sanitized, not no_output)

    @bp.delete(
        "/studies/{uuid}",
        status_code=HTTPStatus.OK,
        tags=[APITag.study_management],
        summary="Delete Study",
    )
    def delete_study(uuid: str, children: bool = False) -> Any:
        logger.info(f"Deleting study {uuid}")
        uuid_sanitized = sanitize_uuid(uuid)

        study_service.delete_study(uuid_sanitized, children)

        return ""

    @bp.put(
        "/studies/{uuid}/owner/{user_id}",
        tags=[APITag.study_permissions],
        summary="Change study owner",
    )
    def change_owner(uuid: str, user_id: int) -> Any:
        logger.info(f"Changing owner to {user_id} for study {uuid}")
        uuid_sanitized = sanitize_uuid(uuid)
        study_service.change_owner(uuid_sanitized, user_id)

        return ""

    @bp.put(
        "/studies/{uuid}/groups/{group_id}",
        tags=[APITag.study_permissions],
        summary="Add a group association",
    )
    def add_group(uuid: str, group_id: str) -> Any:
        logger.info(f"Adding group {group_id} to study {uuid}")
        uuid_sanitized = sanitize_uuid(uuid)
        group_id = sanitize_string(group_id)
        study_service.add_group(uuid_sanitized, group_id)

        return ""

    @bp.delete(
        "/studies/{uuid}/groups/{group_id}",
        tags=[APITag.study_permissions],
        summary="Remove a group association",
    )
    def remove_group(uuid: str, group_id: str) -> Any:
        logger.info(f"Removing group {group_id} to study {uuid}")
        uuid_sanitized = sanitize_uuid(uuid)
        group_id = sanitize_string(group_id)

        study_service.remove_group(uuid_sanitized, group_id)

        return ""

    @bp.put(
        "/studies/{uuid}/public_mode/{mode}",
        tags=[APITag.study_permissions],
        summary="Set study public mode",
    )
    def set_public_mode(uuid: str, mode: PublicMode) -> Any:
        logger.info(f"Setting public mode to {mode} for study {uuid}")
        uuid_sanitized = sanitize_uuid(uuid)
        study_service.set_public_mode(uuid_sanitized, mode)

        return ""

    @bp.get(
        "/studies/_versions",
        tags=[APITag.study_management],
        summary="Show available study versions",
        response_model=List[str],
    )
    def get_study_versions() -> Any:
        logger.info("Fetching version list")
        return StudyService.get_studies_versions()

    @bp.get(
        "/studies/{uuid}",
        tags=[APITag.study_management],
        summary="Get Study information",
        response_model=StudyMetadataDTO,
    )
    def get_study_metadata(uuid: str) -> Any:
        logger.info(f"Fetching study {uuid} metadata")
        study_metadata = study_service.get_study_information(uuid)
        return study_metadata

    @bp.put(
        "/studies/{uuid}",
        tags=[APITag.study_management],
        summary="Update Study information",
        response_model=StudyMetadataDTO,
    )
    def update_study_metadata(uuid: str, study_metadata_patch: StudyMetadataPatchDTO) -> Any:
        logger.info(f"Updating metadata for study {uuid}")
        study_metadata = study_service.update_study_information(uuid, study_metadata_patch)
        return study_metadata

    @bp.put(
        "/studies/{study_id}/archive",
        summary="Archive a study",
        tags=[APITag.study_management],
    )
    def archive_study(study_id: str) -> Any:
        logger.info(f"Archiving study {study_id}")
        study_id = sanitize_uuid(study_id)
        return study_service.archive(study_id)

    @bp.put(
        "/studies/{study_id}/unarchive",
        summary="Unarchive a study",
        tags=[APITag.study_management],
    )
    def unarchive_study(study_id: str) -> Any:
        logger.info(f"Unarchiving study {study_id}")
        study_id = sanitize_uuid(study_id)
        return study_service.unarchive(study_id)

    @bp.get(
        "/studies/{uuid}/disk-usage",
        summary="Compute study disk usage",
        tags=[APITag.study_management],
    )
    def study_disk_usage(uuid: str) -> int:
        """
        Compute disk usage of an input study

        Args:
        - `uuid`: the UUID of the study whose disk usage is to be retrieved.

        Return:
        - The disk usage of the study in bytes.
        """
        logger.info("Retrieving study disk usage")
        return study_service.get_disk_usage(uuid=uuid)

    return bp

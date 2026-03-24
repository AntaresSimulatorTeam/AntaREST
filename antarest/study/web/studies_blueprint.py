# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
import logging
from collections.abc import Sequence
from http import HTTPStatus
from pathlib import PurePosixPath
from typing import Annotated

from antares.study.version import StudyVersion
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from markupsafe import escape
from pydantic import NonNegativeInt

from antarest.core.api_types import SanitizedStr, UuidStr
from antarest.core.exceptions import BadArchiveContent, BadZipBinary, IncorrectArgumentsForCopy
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.model import PublicMode
from antarest.core.utils.archives import ArchiveFormat
from antarest.core.utils.utils import sanitize_string, validate_folder_path, validate_study_name
from antarest.core.utils.web import APITag
from antarest.dependencies import ConfigDep, StudyServiceDep, auth_required
from antarest.login.utils import require_admin_user, require_current_user
from antarest.study.dtos import StudySynthesis
from antarest.study.model import (
    DeleteManyStudies,
    MatrixIndex,
    StorageMode,
    StudyMetadataDTO,
    StudyMetadataPatchDTO,
    StudyRepairRequest,
)
from antarest.study.repository import AccessPermissions, StudyFilter, StudyPagination, StudySortBy
from antarest.study.service import OutputSelection, StudyService

logger = logging.getLogger(__name__)

QUERY_REGEX = r"^\s*(?:\d+\s*(?:,\s*\d+\s*)*)?$"


def _split_comma_separated_values(value: str, *, default: Sequence[str] = ()) -> Sequence[str]:
    """Split a comma-separated list of values into an ordered set of strings."""
    values = value.split(",") if value else default
    # drop whitespace around values
    values = [v.strip() for v in values]
    # remove duplicates and preserve order (to have a deterministic result for unit tests).
    return list(collections.OrderedDict.fromkeys(values))


def create_study_routes() -> APIRouter:
    """
    Endpoint implementation for studies management
    """
    bp = APIRouter(prefix="/v1", tags=[APITag.study_management], dependencies=[Depends(auth_required)])

    @bp.get(
        "/studies",
        summary="Get Studies",
    )
    def get_studies(
        study_service: StudyServiceDep,
        name: Annotated[
            SanitizedStr,
            Query(
                description=(
                    "Filter studies based on their name."
                    "Case-insensitive search for studies whose name contains the specified value."
                ),
                alias="name",
            ),
        ] = "",
        managed: Annotated[bool | None, Query(description="Filter studies based on their management status.")] = None,
        archived: Annotated[bool | None, Query(description="Filter studies based on their archive status.")] = None,
        variant: Annotated[bool | None, Query(description="Filter studies based on their variant status.")] = None,
        versions: Annotated[
            SanitizedStr, Query(description="Comma-separated list of versions for filtering.", pattern=QUERY_REGEX)
        ] = "",
        users: Annotated[
            SanitizedStr, Query(description="Comma-separated list of user IDs for filtering.", pattern=QUERY_REGEX)
        ] = "",
        groups: Annotated[SanitizedStr, Query(description="Comma-separated list of group IDs for filtering.")] = "",
        tags: Annotated[SanitizedStr, Query(description="Comma-separated list of tags for filtering.")] = "",
        study_ids: Annotated[
            SanitizedStr, Query(description="Comma-separated list of study IDs for filtering.", alias="studyIds")
        ] = "",
        exists: Annotated[bool | None, Query(description="Filter studies based on their existence on disk.")] = None,
        workspace: Annotated[SanitizedStr, Query(description="Filter studies based on their workspace.")] = "",
        folder: Annotated[SanitizedStr, Query(description="Filter studies based on their folder.")] = "",
        sort_by: Annotated[
            StudySortBy | None,
            Query(
                description="Sort studies based on their name (case-insensitive) or creation date.",
                alias="sortBy",
            ),
        ] = None,
        page_nb: Annotated[NonNegativeInt, Query(description="Page number (starting from 0).", alias="pageNb")] = 0,
        page_size: Annotated[
            NonNegativeInt, Query(description="Number of studies per page (0 = no limit).", alias="pageSize")
        ] = 0,
    ) -> dict[str, StudyMetadataDTO]:
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
            access_permissions=AccessPermissions.for_current_user(),
        )

        matching_studies = study_service.get_studies_information(
            study_filter=study_filter,
            sort_by=sort_by,
            pagination=StudyPagination(page_nb=page_nb, page_size=page_size),
        )

        return matching_studies

    @bp.get(
        "/studies/count",
        summary="Count Studies",
    )
    def count_studies(
        study_service: StudyServiceDep,
        name: Annotated[
            SanitizedStr, Query(description="Case-insensitive: filter studies based on their name.", alias="name")
        ] = "",
        managed: Annotated[bool | None, Query(description="Management status filter.")] = None,
        archived: Annotated[bool | None, Query(description="Archive status filter.")] = None,
        variant: Annotated[bool | None, Query(description="Variant status filter.")] = None,
        versions: Annotated[
            SanitizedStr, Query(description="Comma-separated versions filter.", pattern=QUERY_REGEX)
        ] = "",
        users: Annotated[SanitizedStr, Query(description="Comma-separated user IDs filter.", pattern=QUERY_REGEX)] = "",
        groups: Annotated[SanitizedStr, Query(description="Comma-separated group IDs filter.")] = "",
        tags: Annotated[SanitizedStr, Query(description="Comma-separated tags filter.")] = "",
        study_ids: Annotated[
            SanitizedStr, Query(description="Comma-separated study IDs filter.", alias="studyIds")
        ] = "",
        exists: Annotated[bool | None, Query(description="Existence on disk filter.")] = None,
        workspace: Annotated[SanitizedStr, Query(description="Workspace filter.")] = "",
        folder: Annotated[SanitizedStr, Query(description="Study folder filter.")] = "",
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
                access_permissions=AccessPermissions.for_current_user(),
            ),
        )

        return count

    @bp.post(
        "/studies/_import",
        status_code=HTTPStatus.CREATED,
        summary="Import Study",
    )
    def import_study(study_service: StudyServiceDep, study: UploadFile, groups: SanitizedStr = "") -> str:
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

        user = require_current_user()
        group_ids_raw = _split_comma_separated_values(groups, default=[group.id for group in user.groups])
        group_ids = [sanitize_string(gid) for gid in group_ids_raw]

        try:
            uuid = study_service.import_study(study.file, group_ids)
        except BadArchiveContent as e:
            raise BadZipBinary(str(e))

        return uuid

    @bp.put(
        "/studies/{uuid}/upgrade",
        status_code=HTTPStatus.OK,
        summary="Upgrade study to the target version (or next version if not specified)",
    )
    def upgrade_study(study_service: StudyServiceDep, uuid: SanitizedStr, target_version: SanitizedStr = "") -> str:
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

    def _output_selection(with_outputs: bool | None, output_ids: list[str]) -> OutputSelection:
        """
        Translates API input to OutputSelection type.

        Output copy behavior:
            - If `with_outputs` is True and `output_ids` are specified: only the specified outputs are copied.
            - If `with_outputs` is True and `output_ids` is empty: all outputs are copied.
            - If `with_outputs` is False and `output_ids` are specified: an error is raised (incoherent configuration).
            - If `with_outputs` is False: no outputs are copied
            - If `with_outputs` is None and `output_ids` are specified: outputs will be copied; behaves like `with_outputs=True`.
            - If `with_outputs` is None and `output_ids` is empty: no outputs are copied.
        """
        if with_outputs is False and output_ids:
            raise IncorrectArgumentsForCopy("output_ids can only be used with with_outputs=True")
        if with_outputs:
            if output_ids:
                return output_ids
            else:
                return "all"
        elif with_outputs is None:
            return output_ids if output_ids else []
        else:
            return []

    @bp.post(
        "/studies/{uuid}/copy",
        status_code=HTTPStatus.CREATED,
        summary="Copy Study",
    )
    def copy_study(
        study_service: StudyServiceDep,
        uuid: SanitizedStr,
        study_name: SanitizedStr,
        output_ids: Annotated[list[SanitizedStr], Query(default_factory=list)],
        with_outputs: bool | None = None,
        groups: SanitizedStr = "",
        use_task: bool = True,
        destination_folder: SanitizedStr = "",
    ) -> str:
        """
        This endpoint enables you to duplicate a study and place it in a specified location.
        You can, for instance, copy a non-managed study to a managed workspace.

        Args:
        - `uuid`: The identifier of the study you wish to duplicate.
        - `study_name`: The name of the new study.
        - `with_outputs`: Indicates whether the study's outputs should also be duplicated.
        - `groups`: Specifies the groups to which your duplicated study will be assigned.
        - `use_task`: Determines whether this duplication operation should trigger a task.
            It is recommended and set as the default value: True.
        - `destination_folder`: The destination path where the study will be copied.
        - `output_ids`: A list of output names that you want to include in the destination study.

        Returns:
        - The unique identifier of the task copying the study.
        """
        logger.info(f"Copying study {uuid} into new study '{study_name}'")

        user = require_current_user()
        group_ids_raw = _split_comma_separated_values(groups, default=[group.id for group in user.groups])
        group_ids = [sanitize_string(gid) for gid in group_ids_raw]

        destination_name_sanitized = validate_study_name(escape(study_name))

        output_selection = _output_selection(with_outputs, output_ids)

        task_id = study_service.copy_study(
            src_uuid=uuid,
            dest_study_name=destination_name_sanitized,
            group_ids=group_ids,
            use_task=use_task,
            destination_folder=PurePosixPath(destination_folder),
            outputs_selection=output_selection,
        )

        return task_id

    @bp.put(
        "/studies/{uuid}/move",
        summary="Move study",
    )
    def move_study(study_service: StudyServiceDep, uuid: SanitizedStr, folder_dest: SanitizedStr) -> None:
        logger.info(f"Moving study {uuid} into folder '{folder_dest}'")
        study_service.move_study(uuid, validate_folder_path(folder_dest))

    @bp.post(
        "/studies",
        status_code=HTTPStatus.CREATED,
        summary="Create a new empty study",
    )
    def create_study(
        study_service: StudyServiceDep,
        config: ConfigDep,
        name: SanitizedStr,
        version: SanitizedStr | None = None,
        groups: SanitizedStr = "",
        directory: Annotated[
            SanitizedStr,
            Query(description="Directory path where the study will be created (e.g., 'project/subfolder')"),
        ] = "",
        storage_mode: StorageMode = StorageMode.FILESYSTEM,
    ) -> str:
        """
        Create a new empty study.

        Args:
        - `name`: The name of the study to create.
        - `version`: The version of the study (optional).
        - `groups`: Comma-separated list of group IDs to associate with the study.
        - `storage_mode`: Storage mode for the study ("filesystem" or "database"). Defaults to "filesystem".
        - `directory`: The name of the directory
        Returns:
        - The ID of the newly created study.
        """
        if storage_mode == StorageMode.DATABASE and not config.storage.study_storage.database_mode_enabled:
            raise HTTPException(
                status_code=HTTPStatus.NOT_IMPLEMENTED,
                detail="Database storage mode is not enabled on this server",
            )
        study_version = StudyVersion.parse(version) if version else None
        logger.info(f"Creating new study '{name}' with storage_mode={storage_mode}")
        name_sanitized = validate_study_name(escape(name))
        group_ids = _split_comma_separated_values(groups)
        group_ids = [sanitize_string(gid) for gid in group_ids]

        directory_path_sanitized = validate_folder_path(directory) if directory else ""

        uuid = study_service.create_study(
            name_sanitized, study_version, group_ids, storage_mode=storage_mode, directory=directory_path_sanitized
        )

        return uuid

    @bp.get(
        "/studies/{uuid}/synthesis",
        summary="Return study synthesis",
    )
    def get_study_synthesis(study_service: StudyServiceDep, uuid: str) -> StudySynthesis:
        study_id = sanitize_string(uuid)
        logger.info(f"Return a synthesis for study '{study_id}'")
        return study_service.get_study_synthesis(study_id)

    @bp.get(
        "/studies/{uuid}/matrixindex",
        summary="Return study input matrix start date index",
    )
    def get_study_matrix_index(
        study_service: StudyServiceDep, uuid: SanitizedStr, path: SanitizedStr = ""
    ) -> MatrixIndex:
        logger.info(f"Return the start date for input matrix '{uuid}'")
        return study_service.get_input_matrix_startdate(uuid, path)

    @bp.get(
        "/studies/{uuid}/export",
        summary="Export Study",
    )
    def export_study(
        study_service: StudyServiceDep,
        uuid: SanitizedStr,
        no_output: bool | None = False,
        compression: ArchiveFormat = ArchiveFormat.ZIP,
    ) -> FileDownloadTaskDTO:
        logger.info(f"Exporting study {uuid}")

        return study_service.export_study(uuid, not no_output, compression)

    @bp.delete(
        "/studies/{uuid}",
        status_code=HTTPStatus.OK,
        summary="Delete Study",
    )
    def delete_study(study_service: StudyServiceDep, uuid: SanitizedStr, children: bool = False) -> None:
        logger.info(f"Deleting study {uuid}")
        study_service.delete_study(uuid, children)

    @bp.delete(
        "/studies",
        status_code=HTTPStatus.NO_CONTENT,
        summary="Delete Multiple Studies",
    )
    def delete_studies(study_service: StudyServiceDep, data: DeleteManyStudies) -> None:
        logger.info(f"Deleting multiple studies: {data.study_ids}")
        study_service.delete_studies(data.study_ids, data.with_variants)

    @bp.put(
        "/studies/{uuid}/owner/{user_id}",
        tags=[APITag.study_permissions],
        summary="Change study owner",
    )
    def change_owner(study_service: StudyServiceDep, uuid: SanitizedStr, user_id: int) -> None:
        logger.info(f"Changing owner to {user_id} for study {uuid}")
        study_service.change_owner(uuid, user_id)

    @bp.put(
        "/studies/{uuid}/groups/{group_id}",
        tags=[APITag.study_permissions],
        summary="Add a group association",
    )
    def add_group(study_service: StudyServiceDep, uuid: SanitizedStr, group_id: SanitizedStr) -> None:
        logger.info(f"Adding group {group_id} to study {uuid}")
        group_id = sanitize_string(group_id)
        study_service.add_group(uuid, group_id)

    @bp.delete(
        "/studies/{uuid}/groups/{group_id}",
        tags=[APITag.study_permissions],
        summary="Remove a group association",
    )
    def remove_group(study_service: StudyServiceDep, uuid: SanitizedStr, group_id: SanitizedStr) -> None:
        logger.info(f"Removing group {group_id} to study {uuid}")
        group_id = sanitize_string(group_id)

        study_service.remove_group(uuid, group_id)

    @bp.put(
        "/studies/{uuid}/public_mode/{mode}",
        tags=[APITag.study_permissions],
        summary="Set study public mode",
    )
    def set_public_mode(study_service: StudyServiceDep, uuid: SanitizedStr, mode: PublicMode) -> None:
        logger.info(f"Setting public mode to {mode} for study {uuid}")
        study_service.set_public_mode(uuid, mode)

    @bp.get(
        "/studies/_versions",
        summary="Show available study versions",
    )
    def get_study_versions() -> list[str]:
        logger.info("Fetching version list")
        return StudyService.get_studies_versions()

    @bp.get(
        "/studies/{uuid}",
        summary="Get Study information",
    )
    def get_study_metadata(study_service: StudyServiceDep, uuid: SanitizedStr) -> StudyMetadataDTO:
        logger.info(f"Fetching study {uuid} metadata")
        study_metadata = study_service.get_study_information(uuid)
        return study_metadata

    @bp.put(
        "/studies/{uuid}",
        summary="Update Study information",
    )
    def update_study_metadata(
        study_service: StudyServiceDep,
        uuid: SanitizedStr,
        study_metadata_patch: StudyMetadataPatchDTO,
    ) -> StudyMetadataDTO:
        logger.info(f"Updating metadata for study {uuid}")
        if study_metadata_patch.name:
            study_metadata_patch.name = validate_study_name(study_metadata_patch.name)
        study_metadata = study_service.update_study_information(uuid, study_metadata_patch)
        return study_metadata

    @bp.put(
        "/studies/{study_id}/archive",
        summary="Archive a study",
    )
    def archive_study(study_service: StudyServiceDep, study_id: UuidStr) -> str:
        logger.info(f"Archiving study {study_id}")
        return study_service.archive(study_id)

    @bp.put(
        "/studies/{study_id}/unarchive",
        summary="Unarchive a study",
    )
    def unarchive_study(study_service: StudyServiceDep, study_id: UuidStr) -> str:
        logger.info(f"Unarchiving study {study_id}")
        return study_service.unarchive(study_id)

    @bp.post(
        "/studies/{study_id}/_repair",
        summary="Repair a study",
    )
    def repair_study(study_service: StudyServiceDep, study_id: UuidStr, repair_request: StudyRepairRequest) -> str:
        require_admin_user()
        logger.info(f"Repairing study {study_id}")
        return study_service.repair_study(study_id, repair_request)

    @bp.get(
        "/studies/{uuid}/disk-usage",
        summary="Compute study disk usage",
    )
    def study_disk_usage(study_service: StudyServiceDep, uuid: SanitizedStr) -> int:
        """
        Compute disk usage of an input study

        Args:
        - `uuid`: the UUID of the study whose disk usage is to be retrieved.

        Return:
        - The disk usage of the study in bytes.
        """
        logger.info("Retrieving study disk usage")
        return study_service.get_disk_usage(uuid=uuid)

    @bp.put(
        "/studies/{study_id}/normalize",
        summary="Move study matrices into the matrix-store and replace them with symbolic links.",
    )
    def normalize_study(study_service: StudyServiceDep, study_id: UuidStr) -> None:
        """
        This endpoint iterates over every matrix inside a study.
        For each, it saves them inside the application's matrix-store.
        Then, it replaces the matrix inside the study with a symbolic link to the matrix inside the matrix-store.
        """
        logger.info(f"Normalizing study {study_id}")
        return study_service.normalize_study_by_id(study_id)

    return bp

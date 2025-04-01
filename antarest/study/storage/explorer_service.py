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

import logging
from http import HTTPStatus
from pathlib import Path, PurePosixPath
from typing import List

from fastapi import HTTPException

from antarest.core.config import Config
from antarest.core.exceptions import ExternalWorkspaceDisabled
from antarest.core.model import StudyPermissionType
from antarest.core.requests import RequestParameters
from antarest.core.utils.utils import sanitize_uuid
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    EXTERNAL_WORKSPACE_NAME,
    NonStudyFolderDTO,
    StudyFolder,
    WorkspaceMetadata,
)
from antarest.study.repository import AccessPermissions, StudyFilter
from antarest.study.service import StudyService
from antarest.study.storage.utils import (
    get_folder_from_workspace,
    get_workspace_from_config,
    has_non_study_folder,
    is_non_study_folder,
    is_study_folder,
    should_ignore_folder_for_scan,
)

logger = logging.getLogger(__name__)


class Explorer:
    def __init__(self, config: Config, study_service: StudyService):
        self.config = config
        self.study_service = study_service

    def list_dir(
        self,
        workspace_name: str,
        workspace_directory_path: str,
    ) -> List[NonStudyFolderDTO]:
        """
        return a list of all directories under workspace_directory_path, that aren't studies.
        """
        workspace = get_workspace_from_config(self.config, workspace_name, default_allowed=False)
        directory_path = get_folder_from_workspace(workspace, workspace_directory_path)
        directories = []
        try:
            # this block is skipped in case of permission error
            children = list(directory_path.iterdir())
            for child in children:
                # if we can't access one child we skip it
                try:
                    if is_non_study_folder(child, workspace.filter_in, workspace.filter_out):
                        # we don't want to expose the full absolute path on the server
                        child_rel_path = PurePosixPath(child.relative_to(workspace.path))
                        has_children = has_non_study_folder(child, workspace.filter_in, workspace.filter_out)
                        directories.append(
                            NonStudyFolderDTO(
                                path=child_rel_path,
                                workspace=workspace_name,
                                name=child.name,
                                has_children=has_children,
                            )
                        )
                except PermissionError as e:
                    logger.warning(f"Permission error while accessing {child} or one of its children: {e}")
        except PermissionError as e:
            logger.warning(f"Permission error while listing {directory_path}: {e}")
        return directories

    def list_workspaces(
        self,
    ) -> List[WorkspaceMetadata]:
        """
        Return the list of all configured workspace name, except the default one.
        """
        return [
            WorkspaceMetadata(name=workspace_name)
            for workspace_name in self.config.storage.workspaces.keys()
            if workspace_name != DEFAULT_WORKSPACE_NAME
        ]

    def open_external_study(self, path: Path, params: RequestParameters) -> str:
        # check that desktop_mode is enabled in config
        if not self.config.desktop_mode:
            logger.warning("Called open api when desktop mode was off")
            raise ExternalWorkspaceDisabled("Desktop mode is not enabled in the configuration")

        # check path is a study folder and we have read permission
        if not is_study_folder(path):
            raise HTTPException(HTTPStatus.UNPROCESSABLE_ENTITY, f"Path {path} is not a study folder")

        # check path is not in a filtered folder
        if should_ignore_folder_for_scan(path, [".*"], []):
            raise HTTPException(HTTPStatus.UNPROCESSABLE_ENTITY, "Cannot open a file in a filtered folder")

        # check if path is inside the default workspace folder
        default_workspace = get_workspace_from_config(self.config, DEFAULT_WORKSPACE_NAME, default_allowed=True)
        if default_workspace.path in path.parents:
            raise HTTPException(
                HTTPStatus.UNPROCESSABLE_ENTITY,
                f"Path {path} is inside the default workspace folder and cannot be opened as an external study",
            )

        # check study doens't already exist
        folder = f"{EXTERNAL_WORKSPACE_NAME}{path}"
        study_count = self.study_service.count_studies(
            StudyFilter(folder=folder, access_permissions=AccessPermissions.from_params(params))
        )
        if study_count > 0:
            raise HTTPException(HTTPStatus.UNPROCESSABLE_ENTITY, f"Study at {path} already exists in database")

        # create a study object from the path
        study_folder = StudyFolder(path=path, workspace=EXTERNAL_WORKSPACE_NAME, groups=[])
        study_id = self.study_service.create_external_study(study_folder, params)
        logger.info(f"External study at {path} successfully created with study id  {study_id}")

        return study_id

    def close_external_study(self, uuid: str, params: RequestParameters) -> None:
        # check that desktop_mode is enabled in config
        if not self.config.desktop_mode:
            logger.warning("Called open api when desktop mode was off")
            raise ExternalWorkspaceDisabled("Study mode is not enabled in the configuration")

        sanitized_uuid = sanitize_uuid(uuid)

        # create a study object from the path
        logger.info(f"Study {sanitized_uuid} will be deleted")
        study = self.study_service.check_study_access(sanitized_uuid, StudyPermissionType.WRITE, params)
        self.study_service.delete_external_study(study)

# Copyright (c) 2024, RTE (https://www.rte-france.com)
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
from typing import List

from antarest.core.config import Config
from antarest.study.model import DEFAULT_WORKSPACE_NAME, NonStudyFolder, WorkspaceMetadata
from antarest.study.storage.utils import (
    get_folder_from_workspace,
    get_workspace_from_config,
    is_study_folder,
    should_ignore_folder_for_scan,
)

logger = logging.getLogger(__name__)


class Explorer:
    def __init__(self, config: Config):
        self.config = config

    def list_dir(
        self,
        workspace_name: str,
        workspace_directory_path: str,
    ) -> List[NonStudyFolder]:
        """
        return a list of all directories under workspace_directory_path, that aren't studies.
        """
        workspace = get_workspace_from_config(self.config, workspace_name, default_allowed=False)
        directory_path = get_folder_from_workspace(workspace, workspace_directory_path)
        directories = []
        try:
            children = list(directory_path.iterdir())
        except PermissionError:
            children = []  # we don't want to try to read folders we can't access
        for child in children:
            if (
                child.is_dir()
                and not is_study_folder(child)
                and not should_ignore_folder_for_scan(child)
                and not child.name.startswith((".", "$"))
            ):
                # we don't want to expose the full absolute path on the server
                child_rel_path = child.relative_to(workspace.path)
                directories.append(NonStudyFolder(path=child_rel_path, workspace=workspace_name, name=child.name))
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

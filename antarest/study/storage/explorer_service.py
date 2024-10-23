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
from antarest.study.model import DEFAULT_WORKSPACE_NAME, NonStudyFolder
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
        workspace = get_workspace_from_config(self.config, workspace_name)
        directory_path = get_folder_from_workspace(workspace, workspace_directory_path)
        directories = []
        for child in directory_path.iterdir():
            if child.is_dir() and not is_study_folder(child) and not should_ignore_folder_for_scan(child):
                directories.append(NonStudyFolder(path=str(child), workspace=workspace_name, name=child.name))
        return directories

    def list_workspaces(
        self,
    ) -> List[str]:
        """
        Return the list of all configured workspace name, except the default one.
        """
        return [
            workspace_name
            for workspace_name in self.config.storage.workspaces.keys()
            if workspace_name != DEFAULT_WORKSPACE_NAME
        ]

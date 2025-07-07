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

import ctypes
import logging
import os
import sys
from pathlib import PurePosixPath
from typing import List

from antarest.core.config import Config
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    FolderDTO,
    WorkspaceMetadata,
)
from antarest.study.storage.utils import (
    get_folder_from_workspace,
    get_workspace_from_config,
    has_children,
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
        show_hidden_file: bool = False,
    ) -> List[FolderDTO]:
        """
        return a list of all directories under workspace_directory_path.
        """
        workspace = get_workspace_from_config(self.config, workspace_name, default_allowed=False)
        directory_path = get_folder_from_workspace(workspace, workspace_directory_path)
        folders = []
        try:
            # this block is skipped in case of permission error
            children = list(directory_path.iterdir())
            for child in children:
                # if we can't access one child we skip it
                try:
                    show = show_hidden_file or not child.name.startswith(".")
                    if show and not should_ignore_folder_for_scan(child, workspace.filter_in, workspace.filter_out):
                        child_rel_path = PurePosixPath(child.relative_to(workspace.path))
                        if is_study_folder(child):
                            has_children_flag = False
                            is_study_folder_flag = True
                        else:
                            has_children_flag = has_children(child, workspace.filter_in, workspace.filter_out)
                            is_study_folder_flag = False
                        folders.append(
                            FolderDTO(
                                path=child_rel_path,
                                workspace=workspace_name,
                                name=child.name,
                                has_children=has_children_flag,
                                is_study_folder=is_study_folder_flag,
                            )
                        )
                except (PermissionError, OSError) as e:
                    logger.warning(f"Error while accessing {child} or one of its children: {e}")
        except (PermissionError, OSError) as e:
            logger.warning(f"Error while listing {directory_path}: {e}")

        return folders

    def list_workspaces(self) -> List[WorkspaceMetadata]:
        """
        Return the list of all configured workspace names, except the default one.
        On Windows, includes the disk name (volume label) in WorkspaceMetadata.
        """
        result = []
        for workspace_name in self.config.storage.workspaces.keys():
            if workspace_name == DEFAULT_WORKSPACE_NAME:
                continue

            disk_name = None
            if sys.platform == "win32":
                drive_letter = os.path.splitdrive(workspace_name)[0] + "\\"
                disk_name = get_volume_label(drive_letter)

            result.append(WorkspaceMetadata(name=workspace_name, disk_name=disk_name))

        return result


def get_volume_label(drive_letter: str) -> str:
    """
    Returns the volume label for a given drive letter like 'C:\\'.
    """
    if not drive_letter.endswith("\\"):
        drive_letter += "\\"
    volume_name_buffer = ctypes.create_unicode_buffer(1024)
    file_system_name_buffer = ctypes.create_unicode_buffer(1024)
    serial_number = ctypes.c_ulong()
    max_component_length = ctypes.c_ulong()
    file_system_flags = ctypes.c_ulong()

    result = ctypes.windll.kernel32.GetVolumeInformationW(  # type: ignore[attr-defined]
        ctypes.c_wchar_p(drive_letter),
        volume_name_buffer,
        ctypes.sizeof(volume_name_buffer),
        ctypes.byref(serial_number),
        ctypes.byref(max_component_length),
        ctypes.byref(file_system_flags),
        file_system_name_buffer,
        ctypes.sizeof(file_system_name_buffer),
    )

    if result:
        return volume_name_buffer.value
    return drive_letter  # fallback

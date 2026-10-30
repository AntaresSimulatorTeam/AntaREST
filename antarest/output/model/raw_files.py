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
from collections.abc import Iterable
from pathlib import PurePosixPath

from antarest.core.serde import AntaresBaseModel


class OutputRawFolderTree(AntaresBaseModel):
    name: str
    files: list[str]
    directories: list["OutputRawFolderTree"]


class OutputRawFilesTree(AntaresBaseModel):
    """
    Tree structure of the files of an output, as written by the simulator.
    """

    files: list[str]
    directories: list[OutputRawFolderTree]


def build_raw_files_tree(files: Iterable[PurePosixPath]) -> OutputRawFilesTree:
    """
    Builds the tree structure of the given relative file paths, preserving their order.
    """
    tree = OutputRawFilesTree(files=[], directories=[])
    folders: dict[PurePosixPath, OutputRawFilesTree | OutputRawFolderTree] = {PurePosixPath(): tree}
    for file in files:
        # Creates the missing parent folders, from the root to the direct parent
        for folder_path in reversed(file.parents):
            if folder_path not in folders:
                folder = OutputRawFolderTree(name=folder_path.name, files=[], directories=[])
                folders[folder_path.parent].directories.append(folder)
                folders[folder_path] = folder
        folders[file.parent].files.append(file.name)
    return tree

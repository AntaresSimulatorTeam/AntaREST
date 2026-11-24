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
from pathlib import PurePosixPath

from antarest.core.serde import AntaresBaseModel


class FolderTree(AntaresBaseModel):
    name: str
    files: list[str]
    directories: list["FolderTree"]


class FilesTree(AntaresBaseModel):
    """
    Tree structure of the files and folders contained in a root folder.
    """

    files: list[str]
    directories: list[FolderTree]


class FilesTreeBuilder:
    """
    Builds a `FilesTree` from paths relative to the root folder, preserving their insertion order.
    """

    def __init__(self) -> None:
        self.tree = FilesTree(files=[], directories=[])
        self._folders: dict[PurePosixPath, FilesTree | FolderTree] = {PurePosixPath(): self.tree}

    def add_folder(self, path: PurePosixPath) -> FilesTree | FolderTree:
        """
        Adds the folder, and its missing parent folders, to the tree. Returns the folder.
        """
        # From the root to the folder itself
        for folder_path in [*reversed(path.parents), path]:
            if folder_path not in self._folders:
                folder = FolderTree(name=folder_path.name, files=[], directories=[])
                self._folders[folder_path.parent].directories.append(folder)
                self._folders[folder_path] = folder
        return self._folders[path]

    def add_file(self, path: PurePosixPath) -> None:
        """
        Adds the file, and its missing parent folders, to the tree.
        """
        self.add_folder(path.parent).files.append(path.name)

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

from antarest.core.files_tree import FilesTree, FilesTreeBuilder, FolderTree


def _build_files_tree(files: list[PurePosixPath]) -> FilesTree:
    builder = FilesTreeBuilder()
    for file in files:
        builder.add_file(file)
    return builder.tree


def test_build_files_tree_empty() -> None:
    assert _build_files_tree([]) == FilesTree(files=[], directories=[])


def test_build_files_tree() -> None:
    files = [
        PurePosixPath("economy/mc-all/areas/fr/values-hourly.txt"),
        PurePosixPath("economy/mc-all/grid/digest.txt"),
        PurePosixPath("gems-views/simulation_table.csv"),
        PurePosixPath("info.antares-output"),
        PurePosixPath("simulation.log"),
    ]
    assert _build_files_tree(files) == FilesTree(
        files=["info.antares-output", "simulation.log"],
        directories=[
            FolderTree(
                name="economy",
                files=[],
                directories=[
                    FolderTree(
                        name="mc-all",
                        files=[],
                        directories=[
                            FolderTree(
                                name="areas",
                                files=[],
                                directories=[FolderTree(name="fr", files=["values-hourly.txt"], directories=[])],
                            ),
                            FolderTree(name="grid", files=["digest.txt"], directories=[]),
                        ],
                    )
                ],
            ),
            FolderTree(name="gems-views", files=["simulation_table.csv"], directories=[]),
        ],
    )


def test_build_files_tree_preserves_order() -> None:
    files = [
        PurePosixPath("simulation.log"),
        PurePosixPath("economy/b.txt"),
        PurePosixPath("info.antares-output"),
        PurePosixPath("adequacy/a.txt"),
        PurePosixPath("economy/a.txt"),
    ]
    assert _build_files_tree(files) == FilesTree(
        files=["simulation.log", "info.antares-output"],
        directories=[
            FolderTree(name="economy", files=["b.txt", "a.txt"], directories=[]),
            FolderTree(name="adequacy", files=["a.txt"], directories=[]),
        ],
    )


def test_build_files_tree_same_folder_name_in_different_parents() -> None:
    files = [
        PurePosixPath("economy/mc-all/values.txt"),
        PurePosixPath("adequacy/mc-all/values.txt"),
    ]
    assert _build_files_tree(files) == FilesTree(
        files=[],
        directories=[
            FolderTree(
                name="economy",
                files=[],
                directories=[FolderTree(name="mc-all", files=["values.txt"], directories=[])],
            ),
            FolderTree(
                name="adequacy",
                files=[],
                directories=[FolderTree(name="mc-all", files=["values.txt"], directories=[])],
            ),
        ],
    )


def test_add_folder() -> None:
    builder = FilesTreeBuilder()
    builder.add_folder(PurePosixPath("empty"))
    builder.add_file(PurePosixPath("folder/file.txt"))
    # Already added folders are not duplicated
    builder.add_folder(PurePosixPath("folder"))
    builder.add_folder(PurePosixPath("empty"))
    assert builder.tree == FilesTree(
        files=[],
        directories=[
            FolderTree(name="empty", files=[], directories=[]),
            FolderTree(name="folder", files=["file.txt"], directories=[]),
        ],
    )

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

from antarest.output.model.raw_files import OutputRawFilesTree, OutputRawFolderTree, build_raw_files_tree


def test_build_raw_files_tree_empty() -> None:
    assert build_raw_files_tree([]) == OutputRawFilesTree(files=[], directories=[])


def test_build_raw_files_tree() -> None:
    files = [
        PurePosixPath("economy/mc-all/areas/fr/values-hourly.txt"),
        PurePosixPath("economy/mc-all/grid/digest.txt"),
        PurePosixPath("gems-views/simulation_table.csv"),
        PurePosixPath("info.antares-output"),
        PurePosixPath("simulation.log"),
    ]
    assert build_raw_files_tree(files) == OutputRawFilesTree(
        files=["info.antares-output", "simulation.log"],
        directories=[
            OutputRawFolderTree(
                name="economy",
                files=[],
                directories=[
                    OutputRawFolderTree(
                        name="mc-all",
                        files=[],
                        directories=[
                            OutputRawFolderTree(
                                name="areas",
                                files=[],
                                directories=[
                                    OutputRawFolderTree(name="fr", files=["values-hourly.txt"], directories=[])
                                ],
                            ),
                            OutputRawFolderTree(name="grid", files=["digest.txt"], directories=[]),
                        ],
                    )
                ],
            ),
            OutputRawFolderTree(name="gems-views", files=["simulation_table.csv"], directories=[]),
        ],
    )


def test_build_raw_files_tree_preserves_order() -> None:
    files = [
        PurePosixPath("simulation.log"),
        PurePosixPath("economy/b.txt"),
        PurePosixPath("info.antares-output"),
        PurePosixPath("adequacy/a.txt"),
        PurePosixPath("economy/a.txt"),
    ]
    assert build_raw_files_tree(files) == OutputRawFilesTree(
        files=["simulation.log", "info.antares-output"],
        directories=[
            OutputRawFolderTree(name="economy", files=["b.txt", "a.txt"], directories=[]),
            OutputRawFolderTree(name="adequacy", files=["a.txt"], directories=[]),
        ],
    )


def test_build_raw_files_tree_same_folder_name_in_different_parents() -> None:
    files = [
        PurePosixPath("economy/mc-all/values.txt"),
        PurePosixPath("adequacy/mc-all/values.txt"),
    ]
    assert build_raw_files_tree(files) == OutputRawFilesTree(
        files=[],
        directories=[
            OutputRawFolderTree(
                name="economy",
                files=[],
                directories=[OutputRawFolderTree(name="mc-all", files=["values.txt"], directories=[])],
            ),
            OutputRawFolderTree(
                name="adequacy",
                files=[],
                directories=[OutputRawFolderTree(name="mc-all", files=["values.txt"], directories=[])],
            ),
        ],
    )


def test_build_raw_files_tree_deep() -> None:
    folder_names = [f"level-{i}" for i in range(20)]
    tree = build_raw_files_tree([PurePosixPath(*folder_names, "file.txt")])

    folder: OutputRawFilesTree | OutputRawFolderTree = tree
    for name in folder_names:
        assert folder.files == []
        assert [d.name for d in folder.directories] == [name]
        folder = folder.directories[0]
    assert folder.files == ["file.txt"]
    assert folder.directories == []

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

from pathlib import Path
from unittest.mock import Mock

from antarest.study.storage.rawstudy.model.filesystem.bucket_node import BucketNode, RegisteredFile
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode


def build_bucket(tmp: Path) -> Path:
    bucket = tmp / "user"
    bucket.mkdir()
    (bucket / "fileA.txt").write_text("Content A")
    (bucket / "fileB.txt").touch()
    (bucket / "folder").mkdir()
    (bucket / "folder/fileC.txt").touch()
    (bucket / "registered_file.ini").touch()
    (bucket / "registered_folder_node").mkdir()

    return bucket


def test_get_bucket(tmp_path: Path):
    registered_files = [
        RegisteredFile(
            key="registered_file",
            node=IniFileNode,
            filename="registered_file.ini",
        ),
        # "registered_folder_node": FolderNode,
    ]

    file = build_bucket(tmp_path)

    resolver = Mock()
    resolver.build_studyfile_uri.side_effect = [
        "fileA.txt",
        "fileB.txt",
        "fileC.txt",
    ]

    context = ContextServer(resolver=resolver, matrix=Mock())

    node = BucketNode(
        config=FileStudyTreeConfig(study_path=file, path=file, study_id="id", version=-1),
        context=context,
        registered_files=registered_files,
    )

    assert node.get(["fileA.txt"]) == b"Content A"
    bucket = node.get()
    assert "fileA.txt" in bucket["fileA.txt"]
    assert "fileB.txt" in bucket["fileB.txt"]
    assert "fileC.txt" in bucket["folder"]["fileC.txt"]
    for registered_file in registered_files:
        assert type(node._get([registered_file.key], get_node=True)) == registered_file.node


def test_save_bucket(tmp_path: Path):
    file = build_bucket(tmp_path)

    node = BucketNode(
        config=FileStudyTreeConfig(study_path=file, path=file, study_id="id", version=-1),
        context=Mock(),
    )
    node.save(data={"fileA.txt": b"Hello, World"})

    assert (file / "fileA.txt").read_text() == "Hello, World"

    node.save(data={"fileC.txt": b"test"}, url=["folder"])
    assert (file / "folder" / "fileC.txt").read_text() == "test"

    node.save(data=b"test2", url=["folder", "fileC.txt"])
    assert (file / "folder" / "fileC.txt").read_text() == "test2"

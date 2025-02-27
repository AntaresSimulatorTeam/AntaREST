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
from zipfile import ZipFile

import pytest
from checksumdir import dirhash
from py7zr import SevenZipFile

from antarest.core.config import Config, StorageConfig
from antarest.core.utils.archives import ArchiveFormat, archive_dir
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService


@pytest.mark.unit_test
def test_export_file(tmp_path: Path):
    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()

    study_service = RawStudyService(
        config=Config(),
        study_factory=Mock(),
        cache=Mock(),
    )
    study_service.check_study_exist = Mock()
    study_service.check_study_exist.return_value = None
    study_service.export_file = Mock()
    study_service.export_file.return_value = b"Hello"

    # Test good study
    md = RawStudy(id=name, workspace=DEFAULT_WORKSPACE_NAME, path=study_path)
    export_path = tmp_path / "export.7z"
    study_service.export_study(md, export_path)


@pytest.mark.unit_test
@pytest.mark.parametrize("outputs", [True, False])
def test_export_archived_study(tmp_path: Path, outputs: bool):
    root = tmp_path / "folder"
    root.mkdir()
    (root / "test").mkdir()
    (root / "test/file.txt").write_text("Bonjour")
    (root / "file.txt").write_text("Hello, World")
    (root / "output/results1").mkdir(parents=True)
    (root / "output/results1/file.txt").write_text("42")

    export_path = tmp_path / "study.7z"

    study_factory = Mock()
    study_service = RawStudyService(
        config=Config(),
        study_factory=study_factory,
        cache=Mock(),
    )

    study = RawStudy(id="Yo", path=root)
    study_tree = Mock()
    study_factory.create_from_fs.return_value = study_tree

    study_service.export_study(study, export_path, outputs=outputs)
    with SevenZipFile(export_path) as szf:
        szf_files = set(szf.getnames())
        assert "file.txt" in szf_files
        assert "test/file.txt" in szf_files
        assert ("output/results1/file.txt" in szf_files) == outputs


@pytest.mark.unit_test
def test_export_flat(tmp_path: Path):
    root = tmp_path / "folder-with-output"
    root.mkdir()
    (root / "test").mkdir()
    (root / "test/file.txt").write_text("Bonjour")
    (root / "test/output").mkdir()
    (root / "test/output/file.txt").write_text("Test")
    (root / "file.txt").write_text("Hello, World")
    (root / "output/result1").mkdir(parents=True)
    (root / "output/result1/file.txt").write_text("42")

    root_without_output = tmp_path / "folder-without-output"
    root_without_output.mkdir()
    (root_without_output / "test").mkdir()
    (root_without_output / "test/file.txt").write_text("Bonjour")
    (root_without_output / "test/output").mkdir()
    (root_without_output / "test/output/file.txt").write_text("Test")
    (root_without_output / "file.txt").write_text("Hello, World")

    root_hash = dirhash(root, "md5")
    root_without_output_hash = dirhash(root_without_output, "md5")

    study_factory = Mock()

    study_service = RawStudyService(
        config=Config(storage=StorageConfig(tmp_dir=tmp_path)),
        study_factory=study_factory,
        cache=Mock(),
    )
    study_tree = Mock()
    study_factory.create_from_fs.return_value = study_tree

    study = RawStudy(id="id", path=root)

    study_service.export_study_flat(study, tmp_path / "copy_with_output", outputs=True)

    copy_with_output_hash = dirhash(tmp_path / "copy_with_output", "md5")

    assert root_hash == copy_with_output_hash

    study_service.export_study_flat(study, tmp_path / "copy_without_output", outputs=False)

    copy_without_output_hash = dirhash(tmp_path / "copy_without_output", "md5")

    assert root_without_output_hash == copy_without_output_hash


@pytest.mark.unit_test
def test_export_output(tmp_path: Path):
    output_id = "output_id"
    root = tmp_path / "folder"
    root.mkdir()
    (root / "test").mkdir()
    (root / "test/file.txt").write_text("Bonjour")
    (root / "file.txt").write_text("Hello, World")
    (root / "output" / output_id).mkdir(parents=True)
    (root / "output" / output_id / "file_output.txt").write_text("42")

    export_path = tmp_path / "study.zip"

    study_factory = Mock()
    study_service = RawStudyService(
        config=Config(),
        study_factory=study_factory,
        cache=Mock(),
    )

    study = RawStudy(id="Yo", path=root)
    study_tree = Mock()
    study_factory.create_from_fs.return_value = study_tree

    study_service.export_output(study, output_id, export_path)
    zipf = ZipFile(export_path)

    assert "file_output.txt" in zipf.namelist()

    # asserts exporting a zipped output doesn't raise an error
    output_path = root / "output" / output_id
    target_path = root / "output" / f"{output_id}.zip"
    archive_dir(output_path, target_path, True, ArchiveFormat.ZIP)
    study_service.export_output(study, output_id, export_path)

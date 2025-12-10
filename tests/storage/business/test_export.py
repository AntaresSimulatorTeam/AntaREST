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
from py7zr import SevenZipFile, py7zr

from antarest.core.config import Config, StorageConfig
from antarest.core.utils.archives import ArchiveFormat, archive_dir
from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapperFactory
from antarest.study.model import DEFAULT_WORKSPACE_NAME
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy, StudyFactory
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.helpers import create_raw_study


def test_export_nominal_case(
    empty_study_930: FileStudy, raw_study_service: RawStudyService, tmp_path: Path, command_context: CommandContext
) -> None:
    # Use the in memory command context inside the raw study_service
    raw_study_service.study_factory = StudyFactory(
        matrix_mapper_factory=MatrixUriMapperFactory(command_context.matrix_service), cache=Mock()
    )
    # Create an area to ensure the matrices are denormalized afterward
    cmd = CreateArea(command_context=command_context, area_name="fr", study_version=empty_study_930.config.version)
    output = cmd.apply(empty_study_930)
    assert output.status
    # Export the study
    study_id = empty_study_930.config.study_id
    study_path = empty_study_930.config.study_path
    study = create_raw_study(id=study_id, workspace=DEFAULT_WORKSPACE_NAME, path=str(study_path))
    export_path = tmp_path / "export.7z"
    assert not export_path.exists()
    raw_study_service.export_study(study, export_path)
    # Ensures the .7z file exists
    assert export_path.exists()
    # Unarchive it to check if the matrix was denormalized well
    extracted_dir_path = export_path.parent / "unarchived_study"
    with py7zr.SevenZipFile(export_path, "r") as szf:
        szf.extractall(path=extracted_dir_path)
    export_path.unlink()
    assert (extracted_dir_path / "input" / "load" / "series" / "load_fr.txt").exists()
    assert not (extracted_dir_path / "input" / "load" / "series" / "load_fr.txt.link").exists()


@pytest.mark.parametrize("outputs", [True, False])
def test_export_archived_study(
    empty_study_930: FileStudy, raw_study_service: RawStudyService, tmp_path: Path, outputs: bool
) -> None:
    study_path = empty_study_930.config.study_path
    (study_path / "output/results1").mkdir(parents=True)
    (study_path / "output/results1/file.txt").write_text("42")

    export_path = tmp_path / "study.7z"

    study = create_raw_study(id=empty_study_930.config.study_id, workspace=DEFAULT_WORKSPACE_NAME, path=str(study_path))

    raw_study_service.export_study(study, export_path, outputs=outputs)
    with SevenZipFile(export_path) as szf:
        szf_files = set(szf.getnames())
        assert ("output/results1/file.txt" in szf_files) == outputs


def test_export_flat(tmp_path: Path) -> None:
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

    study = create_raw_study(id="id", path=root)

    study_service.export_study_flat(study, tmp_path / "copy_with_output", outputs=True)

    copy_with_output_hash = dirhash(tmp_path / "copy_with_output", "md5")

    assert root_hash == copy_with_output_hash

    study_service.export_study_flat(study, tmp_path / "copy_without_output", outputs=False)

    copy_without_output_hash = dirhash(tmp_path / "copy_without_output", "md5")

    assert root_without_output_hash == copy_without_output_hash


def test_export_output(tmp_path: Path) -> None:
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

    study = create_raw_study(id="Yo", path=root)
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

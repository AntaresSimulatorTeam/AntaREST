from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

from checksumdir import dirhash

import pytest

from antarest.core.config import Config
from antarest.storage.business.exporter_service import ExporterService
from antarest.storage.business.raw_study_service import RawStudyService
from antarest.storage.model import Study, DEFAULT_WORKSPACE_NAME, RawStudy


def build_storage_service(workspace: Path, uuid: str) -> RawStudyService:
    service = Mock()
    service.get_workspace_path.return_value = workspace
    service.get_study_path.return_value = workspace / uuid
    return service


@pytest.mark.unit_test
def test_export_file(tmp_path: Path):
    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()

    study_service = Mock()
    study_service.check_study_exist.return_value = None

    exporter_service = ExporterService(
        study_service=build_storage_service(tmp_path, name),
        study_factory=Mock(),
        config=Config(),
    )
    exporter_service.export_file = Mock()
    exporter_service.export_file.return_value = b"Hello"

    # Test good study
    md = RawStudy(id=name, workspace=DEFAULT_WORKSPACE_NAME)
    export_path = tmp_path / "export.zip"
    exporter_service.export_study(md, export_path)
    exporter_service.export_file.assert_called_once_with(
        study_path, export_path, True
    )


@pytest.mark.unit_test
@pytest.mark.parametrize("outputs", [True, False])
def test_export_file(tmp_path: Path, outputs: bool):
    root = tmp_path / "folder"
    root.mkdir()
    (root / "test").mkdir()
    (root / "test/file.txt").write_text("Bonjour")
    (root / "file.txt").write_text("Hello, World")
    (root / "output").mkdir()
    (root / "output/file.txt").write_text("42")

    export_path = tmp_path / "study.zip"

    study_factory = Mock()
    exporter_service = ExporterService(
        study_service=Mock(),
        study_factory=study_factory,
        config=Config(),
    )
    study_tree = Mock()
    study_factory.create_from_fs.return_value = (None, study_tree)

    exporter_service.export_file(root, export_path, outputs)
    zipf = ZipFile(export_path)

    assert "file.txt" in zipf.namelist()
    assert "test/" in zipf.namelist()
    assert "test/file.txt" in zipf.namelist()
    assert ("output/" in zipf.namelist()) == outputs
    assert ("output/file.txt" in zipf.namelist()) == outputs


@pytest.mark.unit_test
def test_export_flat(tmp_path: Path):
    root = tmp_path / "folder-with-output"
    root.mkdir()
    (root / "test").mkdir()
    (root / "test/file.txt").write_text("Bonjour")
    (root / "test/output").mkdir()
    (root / "test/output/file.txt").write_text("Test")
    (root / "file.txt").write_text("Hello, World")
    (root / "output").mkdir()
    (root / "output/file.txt").write_text("42")

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
    exporter_service = ExporterService(
        study_service=Mock(),
        study_factory=study_factory,
        config=Config(tmp_dir=tmp_path),
    )
    study_tree = Mock()
    study_factory.create_from_fs.return_value = (None, study_tree)

    exporter_service.export_flat(
        root, tmp_path / "copy_with_output", outputs=True
    )

    copy_with_output_hash = dirhash(tmp_path / "copy_with_output", "md5")

    assert root_hash == copy_with_output_hash

    exporter_service.export_flat(
        root, tmp_path / "copy_without_output", outputs=False
    )

    copy_without_output_hash = dirhash(tmp_path / "copy_without_output", "md5")

    assert root_without_output_hash == copy_without_output_hash

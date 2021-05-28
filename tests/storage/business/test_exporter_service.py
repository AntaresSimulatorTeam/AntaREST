from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.storage.business.exporter_service import ExporterService
from antarest.storage.business.raw_study_service import RawStudyService
from antarest.storage.model import Study, DEFAULT_WORKSPACE_NAME, RawStudy
from antarest.storage.repository.filesystem.config.model import StudyConfig


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

    exporter = Mock()
    exporter.export_file.return_value = b"Hello"

    study_service = Mock()
    study_service.check_study_exist.return_value = None

    exporter_service = ExporterService(
        study_service=build_storage_service(tmp_path, name),
        study_factory=Mock(),
        exporter=exporter,
    )

    # Test good study
    md = RawStudy(id=name, workspace=DEFAULT_WORKSPACE_NAME)
    assert b"Hello" == exporter_service.export_study(md)
    exporter.export_file.assert_called_once_with(study_path, True)


@pytest.mark.unit_test
def test_export_matrix(tmp_path: Path) -> None:
    file = tmp_path / "file.txt"
    file.write_bytes(b"Hello World")

    service = Mock()
    service.get_study_path.return_value = tmp_path

    exporter = ExporterService(
        study_service=service, study_factory=Mock(), exporter=Mock()
    )

    md = RawStudy(id="id", workspace=DEFAULT_WORKSPACE_NAME)
    assert exporter.get_matrix(md, "file.txt") == b"Hello World"

from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.storage.business.exporter_service import ExporterService
from antarest.storage.business.study_service import StudyService
from antarest.storage.model import Metadata
from antarest.storage.repository.filesystem.config.model import StudyConfig


def build_storage_service(workspace: Path, uuid: str) -> StudyService:
    service = Mock()
    service.get_workspace_path.return_value = workspace
    service.get_study_path.return_value = workspace / uuid
    return service


@pytest.mark.unit_test
def test_export_file(tmp_path: Path, storage_service_builder):
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
    md = Metadata(id=name, workspace="default")
    assert b"Hello" == exporter_service.export_study(md)
    exporter.export_file.assert_called_once_with(study_path, True)


@pytest.mark.unit_test
def test_export_compact_file(tmp_path: Path, storage_service_builder):
    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()

    exporter = Mock()
    exporter.export_compact.return_value = b"Hello"

    study_service = Mock()
    study_service.check_study_exist.return_value = None
    study_service.get.return_value = 42

    factory = Mock()
    factory.create_from_fs.return_value = (
        StudyConfig(study_path=study_path, outputs={42: "value"}),
        study_service,
    )
    factory.create_from_config.return_value = study_service

    exporter_service = ExporterService(
        study_service=build_storage_service(tmp_path, name),
        study_factory=factory,
        exporter=exporter,
    )

    md = Metadata(id=name, workspace="default")
    assert b"Hello" == exporter_service.export_study(
        md, compact=True, outputs=False
    )

    factory.create_from_config.assert_called_once_with(
        StudyConfig(study_path=study_path)
    )
    exporter.export_compact.assert_called_once_with(study_path, 42)

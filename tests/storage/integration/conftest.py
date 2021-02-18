from pathlib import Path
from zipfile import ZipFile

import pytest

from antarest.common.config import Config
from antarest.storage.repository.antares_io.exporter.export_file import (
    Exporter,
)
from antarest.storage.repository.filesystem.factory import StudyFactory
from antarest.storage.service import StorageService


@pytest.fixture
def sta_mini_path(tmp_path: str) -> Path:
    return Path(tmp_path) / "studies" / "STA-mini"


@pytest.fixture
def sta_mini_zip_path(project_path: Path) -> Path:
    return project_path / "examples/studies/STA-mini.zip"


@pytest.fixture
def storage_service(
    tmp_path: str, project_path: Path, sta_mini_zip_path: Path
) -> StorageService:

    path_studies = Path(tmp_path) / "studies"

    path_resources = project_path / "resources"

    with ZipFile(sta_mini_zip_path) as zip_output:
        zip_output.extractall(path=path_studies)

    storage_service = StorageService(
        study_factory=StudyFactory(),
        exporter=Exporter(),
        config=Config(
            {
                "_internal": {"resources_path": path_resources},
                "security": {"disabled": True},
                "storage": {"studies": path_studies},
            }
        ),
    )

    return storage_service

import os
import shutil
from pathlib import Path
import io
from unittest.mock import Mock

import pytest

from antarest.common.config import Config
from antarest.storage.business.importer_service import (
    ImporterService,
    fix_study_root,
)
from antarest.storage.business.study_service import StudyService
from antarest.storage.model import Metadata, DEFAULT_WORKSPACE_NAME
from antarest.storage.web.exceptions import (
    IncorrectPathError,
    BadZipBinary,
    StudyValidationError,
)


def build_storage_service(workspace: Path, uuid: str) -> StudyService:
    service = Mock()
    service.get_workspace_path.return_value = workspace
    service.get_study_path.return_value = workspace / uuid
    return service


@pytest.mark.unit_test
def test_upload_matrix(tmp_path: Path, storage_service_builder) -> None:

    study_uuid = "my-study"
    study_path = tmp_path / study_uuid
    study_path.mkdir()
    (study_path / "study.antares").touch()

    importer_service = ImporterService(
        study_service=build_storage_service(tmp_path, study_uuid),
        study_factory=Mock(),
    )

    study_url = study_uuid + "/"
    matrix_path = "WRONG_MATRIX_PATH"
    md = Metadata(id=study_uuid, workspace=DEFAULT_WORKSPACE_NAME)
    with pytest.raises(IncorrectPathError):
        importer_service.upload_matrix(md, study_url + matrix_path, b"")

    study_url = study_uuid + "/"
    matrix_path = "matrix.txt"
    data = b"hello"
    importer_service.upload_matrix(md, study_url + matrix_path, data)
    assert (study_path / matrix_path).read_bytes() == data


@pytest.mark.unit_test
def test_import_study(tmp_path: Path, storage_service_builder) -> None:

    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()

    study = Mock()
    study.get.return_value = {"study": {"antares": {"version": 700}}}
    study_factory = Mock()
    study_factory.create_from_fs.return_value = None, study

    importer_service = ImporterService(
        study_service=build_storage_service(tmp_path, "other-study"),
        study_factory=study_factory,
    )

    filepath_zip = shutil.make_archive(
        str(study_path.absolute()), "zip", study_path
    )
    shutil.rmtree(study_path)

    path_zip = Path(filepath_zip)

    md = Metadata(id="other-study", workspace=DEFAULT_WORKSPACE_NAME)
    with path_zip.open("rb") as input_file:
        md = importer_service.import_study(md, input_file)
        assert md.path == f"{tmp_path}{os.sep}other-study"

    shutil.rmtree(tmp_path / "other-study")
    with pytest.raises(BadZipBinary):
        importer_service.import_study(md, io.BytesIO(b""))


@pytest.mark.unit_test
def test_fix_root(tmp_path: Path):
    name = "my-study"
    study_path = tmp_path / name
    study_nested_root = study_path / "nested" / "real_root"
    os.makedirs(study_nested_root)
    (study_nested_root / "antares.study").touch()
    # when the study path is a single file
    with pytest.raises(StudyValidationError):
        fix_study_root(study_nested_root / "antares.study")

    shutil.rmtree(study_path)
    study_path = tmp_path / name
    study_nested_root = study_path / "nested" / "real_root"
    os.makedirs(study_nested_root)
    (study_nested_root / "antares.study").touch()
    os.mkdir(study_nested_root / "input")

    fix_study_root(study_path)
    study_files = os.listdir(study_path)
    assert len(study_files) == 2
    assert "antares.study" in study_files and "input" in study_files

    shutil.rmtree(study_path)

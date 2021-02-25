import shutil
from pathlib import Path
import io
from unittest.mock import Mock

import pytest

from antarest.login.model import User, Role
from antarest.storage.business.importer_service import ImporterService
from antarest.storage.business.storage_service_parameters import (
    StorageServiceParameters,
)
from antarest.storage.web.exceptions import (
    StudyNotFoundError,
    IncorrectPathError,
    BadZipBinary,
)


@pytest.mark.unit_test
def test_upload_matrix(tmp_path: Path, storage_service_builder) -> None:

    study_uuid = "my-study"
    study_path = tmp_path / study_uuid
    study_path.mkdir()
    (study_path / "study.antares").touch()

    importer_service = ImporterService(
        path_to_studies=tmp_path, study_service=Mock(), study_factory=Mock()
    )

    study_url = study_uuid + "/"
    matrix_path = "WRONG_MATRIX_PATH"
    with pytest.raises(IncorrectPathError):
        importer_service.upload_matrix(study_url + matrix_path, b"")

    study_url = study_uuid + "/"
    matrix_path = "matrix.txt"
    data = b"hello"
    importer_service.upload_matrix(study_url + matrix_path, data)
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
        path_to_studies=tmp_path,
        study_service=Mock(),
        study_factory=study_factory,
    )

    filepath_zip = shutil.make_archive(
        str(study_path.absolute()), "zip", study_path
    )
    shutil.rmtree(study_path)

    path_zip = Path(filepath_zip)

    with path_zip.open("rb") as input_file:
        uuid = importer_service.import_study(input_file)

    with pytest.raises(BadZipBinary):
        importer_service.import_study(io.BytesIO(b""))

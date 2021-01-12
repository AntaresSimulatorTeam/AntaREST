import io
import shutil
from pathlib import Path
from typing import Callable
from unittest.mock import Mock

import pytest

from api_iso_antares.filesystem.config.model import Config, Simulation
from api_iso_antares.web import RequestHandler
from api_iso_antares.web.html_exception import (
    BadZipBinary,
    IncorrectPathError,
    StudyNotFoundError,
    StudyValidationError,
)
from api_iso_antares.web.request_handler import (
    RequestHandlerParameters,
)


@pytest.mark.unit_test
def test_get(tmp_path: str, project_path) -> None:

    """
    path_to_studies
    |_study1 (d)
    |_ study2.py
        |_ settings (d)
    |_myfile (f)
    """

    # Create folders
    path_to_studies = Path(tmp_path)
    (path_to_studies / "study1").mkdir()
    (path_to_studies / "myfile").touch()
    path_study = path_to_studies / "study2.py"
    path_study.mkdir()
    (path_study / "settings").mkdir()
    (path_study / "study.antares").touch()

    data = {"titi": 43}
    sub_route = "settings"

    path = path_study / "settings"
    key = "titi"

    study = Mock()
    study.get.return_value = data
    study_factory = Mock()
    study_factory.create_from_fs.return_value = (None, study)

    request_handler = RequestHandler(
        study_factory=study_factory,
        exporter=Mock(),
        path_studies=path_to_studies,
        path_resources=project_path / "resources",
    )

    parameters = RequestHandlerParameters(depth=2)

    output = request_handler.get(
        route=f"study2.py/{sub_route}", parameters=parameters
    )

    assert output == data

    study.get.assert_called_once_with(["settings"], depth=2)


@pytest.mark.unit_test
def test_assert_study_exist(tmp_path: str, project_path) -> None:

    tmp = Path(tmp_path)
    (tmp / "study1").mkdir()
    (tmp / "study.antares").touch()
    path_study2 = tmp / "study2.py"
    path_study2.mkdir()
    (path_study2 / "settings").mkdir()
    (path_study2 / "study.antares").touch()
    # Input
    study_name = "study2.py"
    path_to_studies = Path(tmp_path)

    # Test & Verify
    request_handler = RequestHandler(
        study_factory=Mock(),
        exporter=Mock(),
        path_studies=path_to_studies,
        path_resources=project_path / "resources",
    )
    request_handler.assert_study_exist(study_name)


@pytest.mark.unit_test
def test_assert_study_not_exist(tmp_path: str, project_path) -> None:
    # Create folders
    tmp = Path(tmp_path)
    (tmp / "study1").mkdir()
    (tmp / "myfile").touch()
    path_study2 = tmp / "study2.py"
    path_study2.mkdir()
    (path_study2 / "settings").mkdir()

    # Input
    study_name = "study3"
    path_to_studies = Path(tmp_path)

    # Test & Verify
    request_handler = RequestHandler(
        study_factory=Mock(),
        exporter=Mock(),
        path_studies=path_to_studies,
        path_resources=project_path / "resources",
    )
    with pytest.raises(StudyNotFoundError):
        request_handler.assert_study_exist(study_name)


@pytest.mark.unit_test
def test_find_studies(
    tmp_path: str, request_handler_builder: Callable
) -> None:
    # Create folders
    path_studies = Path(tmp_path) / "studies"
    path_studies.mkdir()

    path_study1 = path_studies / "study1"
    path_study1.mkdir()
    (path_study1 / "study.antares").touch()

    path_study2 = path_studies / "study2"
    path_study2.mkdir()
    (path_study2 / "study.antares").touch()

    path_not_study = path_studies / "not_a_study"
    path_not_study.mkdir()
    (path_not_study / "lambda.txt").touch()

    path_lambda = path_studies / "folder1"
    path_lambda.mkdir()
    path_study_misplaced = path_lambda / "study_misplaced"
    path_study_misplaced.mkdir()
    (path_study_misplaced / "study.antares").touch()
    # Input
    study_names = ["study1", "study2"]

    # Test & Verify
    request_handler = request_handler_builder(path_studies=path_studies)

    assert study_names == request_handler.get_study_uuids()


@pytest.mark.unit_test
def test_create_study(
    tmp_path: str, request_handler_builder: Callable, project_path
) -> None:

    path_studies = Path(tmp_path)

    study = Mock()
    data = {"study": {"antares": {"caption": None}}}
    study.get.return_value = data

    study_factory = Mock()
    study_factory.create_from_fs.return_value = (None, study)

    request_handler = request_handler_builder(
        path_studies=path_studies,
        study_factory=study_factory,
        exporter=Mock(),
        path_resources=project_path / "resources",
    )

    study_name = "study1"
    uuid = request_handler.create_study(study_name)

    path_study = path_studies / uuid
    assert path_study.exists()

    path_study_antares_infos = path_study / "study.antares"
    assert path_study_antares_infos.is_file()


@pytest.mark.unit_test
def test_copy_study(
    tmp_path: str,
    clean_ini_writer: Callable,
    request_handler_builder: Callable,
) -> None:

    path_studies = Path(tmp_path)
    source_name = "study1"
    path_study = path_studies / source_name
    path_study.mkdir()
    path_study_info = path_study / "study.antares"
    path_study_info.touch()

    value = {
        "study": {
            "antares": {
                "caption": "ex1",
                "created": 1480683452,
                "lastsave": 1602678639,
                "author": "unknown",
            },
            "output": [],
        }
    }

    study = Mock()
    study.get.return_value = value
    study_factory = Mock()

    config = Mock()
    study_factory.create_from_fs.return_value = config, study
    study_factory.create_from_config.return_value = study

    url_engine = Mock()
    url_engine.resolve.return_value = None, None, None
    request_handler = request_handler_builder(
        study_factory=study_factory,
        path_studies=path_studies,
    )

    destination_name = "study2"
    request_handler.copy_study(source_name, destination_name)

    study.get.assert_called_once_with()


@pytest.mark.unit_test
def test_export_file(tmp_path: Path, request_handler_builder: Callable):
    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()

    exporter = Mock()
    exporter.export_file.return_value = b"Hello"

    request_handler = request_handler_builder(
        exporter=exporter,
        path_studies=tmp_path,
    )

    # Test wrong study
    with pytest.raises(StudyNotFoundError):
        request_handler.export_study("WRONG")

    # Test good study
    assert b"Hello" == request_handler.export_study(name)
    exporter.export_file.assert_called_once_with(study_path, True)


@pytest.mark.unit_test
def test_export_compact_file(tmp_path: Path, request_handler_builder):
    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()

    exporter = Mock()
    exporter.export_compact.return_value = b"Hello"

    study = Mock()
    study.get.return_value = 42

    factory = Mock()
    factory.create_from_fs.return_value = (
        Config(study_path=study_path, outputs={42: "value"}),
        study,
    )
    factory.create_from_config.return_value = study

    request_handler = request_handler_builder(
        study_factory=factory,
        exporter=exporter,
        path_studies=tmp_path,
    )

    assert b"Hello" == request_handler.export_study(
        name, compact=True, outputs=False
    )

    factory.create_from_config.assert_called_once_with(
        Config(study_path=study_path)
    )
    exporter.export_compact.assert_called_once_with(study_path, 42)


@pytest.mark.unit_test
def test_delete_study(
    tmp_path: Path, request_handler_builder: Callable
) -> None:

    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()

    request_handler = request_handler_builder(path_studies=tmp_path)

    request_handler.delete_study(name)

    assert not study_path.exists()


@pytest.mark.unit_test
def test_upload_matrix(
    tmp_path: Path, request_handler_builder: Callable
) -> None:

    study_uuid = "my-study"
    study_path = tmp_path / study_uuid
    study_path.mkdir()
    (study_path / "study.antares").touch()

    request_handler = request_handler_builder(path_studies=tmp_path)

    study_url = "WRONG-STUDY-NAME/"
    matrix_path = ""
    with pytest.raises(StudyNotFoundError):
        request_handler.upload_matrix(study_url + matrix_path, b"")

    study_url = study_uuid + "/"
    matrix_path = "WRONG_MATRIX_PATH"
    with pytest.raises(IncorrectPathError):
        request_handler.upload_matrix(study_url + matrix_path, b"")

    study_url = study_uuid + "/"
    matrix_path = "matrix.txt"
    data = b"hello"
    request_handler.upload_matrix(study_url + matrix_path, data)
    assert (study_path / matrix_path).read_bytes() == data


@pytest.mark.unit_test
def test_import_study(
    tmp_path: Path, request_handler_builder: Callable
) -> None:

    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()

    study = Mock()
    study.get.return_value = {"study": {"antares": {"version": 700}}}
    study_factory = Mock()
    study_factory.create_from_fs.return_value = None, study

    request_handler = request_handler_builder(
        study_factory=study_factory, path_studies=tmp_path
    )

    filepath_zip = shutil.make_archive(
        str(study_path.absolute()), "zip", study_path
    )
    shutil.rmtree(study_path)

    path_zip = Path(filepath_zip)

    with path_zip.open("rb") as input_file:
        uuid = request_handler.import_study(input_file)

    request_handler.assert_study_exist(uuid)
    request_handler.assert_study_not_exist(name)

    with pytest.raises(BadZipBinary):
        request_handler.import_study(io.BytesIO(b""))


@pytest.mark.unit_test
def test_check_antares_version(
    tmp_path: Path, request_handler_builder: Callable
) -> None:

    right_study = {"study": {"antares": {"version": 700}}}
    RequestHandler.check_antares_version(right_study)

    wrong_study = {"study": {"antares": {"version": 600}}}
    with pytest.raises(StudyValidationError):
        RequestHandler.check_antares_version(wrong_study)


@pytest.mark.unit_test
def test_edit_study(tmp_path: Path, request_handler_builder: Callable) -> None:
    # Mock
    (tmp_path / "my-uuid").mkdir()
    (tmp_path / "my-uuid/study.antares").touch()

    study = Mock()
    study_factory = Mock()
    study_factory.create_from_fs.return_value = None, study

    request_handler = request_handler_builder(
        study_factory=study_factory, path_studies=tmp_path
    )

    # Input
    url = "my-uuid/url/to/change"
    new = {"Hello": "World"}

    res = request_handler.edit_study(url, new)

    assert new == res
    study.save.assert_called_once_with(new, ["url", "to", "change"])

import io
import shutil
from pathlib import Path
from typing import Callable
from unittest.mock import Mock

import pytest

from api_iso_antares.antares_io.reader import IniReader
from api_iso_antares.antares_io.writer.ini_writer import IniWriter
from api_iso_antares.custom_types import JSON
from api_iso_antares.engine import FileSystemEngine
from api_iso_antares.jsm import JsonSchema
from api_iso_antares.web import RequestHandler
from api_iso_antares.web.request_handler import (
    RequestHandlerParameters,
)
from api_iso_antares.web.html_exception import (
    BadZipBinary,
    IncorrectPathError,
    StudyNotFoundError,
    StudyValidationError,
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

    jsm = JsonSchema(
        data={"type": "object", "properties": {"titi": {"type": "number"}}}
    )

    path = path_study / "settings"
    key = "titi"
    url_engine_mock = Mock()
    url_engine_mock.resolve.return_value = (jsm, path, key)

    study_reader_mock = Mock()
    study_reader_mock.parse.return_value = data

    jsm_validator_mock = Mock()
    jsm_validator_mock.validate.return_value = None

    request_handler = RequestHandler(
        study_parser=study_reader_mock,
        url_engine=url_engine_mock,
        exporter=Mock(),
        path_studies=path_to_studies,
        path_resources=project_path / "resources",
        jsm_validator=jsm_validator_mock,
    )

    parameters = RequestHandlerParameters(depth=2)

    output = request_handler.get(
        route=f"study2.py/{sub_route}", parameters=parameters
    )

    assert output == data

    study_reader_mock.parse.assert_called_once_with(
        deep_path=path, study_path=path_study, jsm=jsm, keys=key
    )
    # TODO remove before fly
    # jsm_validator_mock.validate.assert_called_once_with(data)
    url_engine_mock.resolve.assert_called_once_with(
        url="settings", path=path_study
    )


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
        study_parser=Mock(),
        url_engine=Mock(),
        exporter=Mock(),
        path_studies=path_to_studies,
        path_resources=project_path / "resources",
        jsm_validator=Mock(),
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
        study_parser=Mock(),
        url_engine=Mock(),
        exporter=Mock(),
        path_studies=path_to_studies,
        path_resources=project_path / "resources",
        jsm_validator=Mock(),
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

    jsm = JsonSchema(data={"type": "number"})
    validator = Mock()
    validator.jsm = jsm

    url_engine = Mock()
    url_engine.resolve.return_value = (None, None, None)

    study_parser = Mock()
    data = {"study": {"antares": {"caption": None}}}
    study_parser.parse.return_value = data

    request_handler = request_handler_builder(
        path_studies=path_studies,
        study_parser=study_parser,
        url_engine=url_engine,
        exporter=Mock(),
        path_resources=project_path / "resources",
        jsm_validator=validator,
    )

    study_name = "study1"
    uuid = request_handler.create_study(study_name)

    path_study = path_studies / uuid
    assert path_study.exists()

    path_study_antares_infos = path_study / "study.antares"
    assert path_study_antares_infos.is_file()

    url_engine.resolve.assert_called_once_with(url="", path=path_study)
    study_parser.write.assert_called_once_with(path_study, data, jsm)


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

    study_parser = Mock()
    study_parser.parse.return_value = value

    reader = Mock()
    reader.read.return_value = value
    study_parser.get_reader.return_value = reader

    writer = Mock()
    study_parser.get_writer.return_value = writer

    jsm = JsonSchema(data={"type": "number"})
    validator = Mock()
    validator.jsm = jsm

    url_engine = Mock()
    url_engine.resolve.return_value = None, None, None
    request_handler = request_handler_builder(
        study_parser=study_parser,
        path_studies=path_studies,
        jsm_validator=validator,
        url_engine=url_engine,
    )

    destination_name = "study2"
    request_handler.copy_study(source_name, destination_name)

    study_parser.parse.assert_called_once_with(
        deep_path=None, jsm=None, keys=None, study_path=path_study
    )
    study_parser.write.assert_called()


@pytest.mark.unit_test
def test_export_file(tmp_path: Path):
    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()

    exporter = Mock()
    exporter.export_file.return_value = b"Hello"

    request_handler = RequestHandler(
        study_parser=Mock(),
        url_engine=Mock(),
        exporter=exporter,
        path_studies=tmp_path,
        path_resources=Mock(),
        jsm_validator=Mock(),
    )

    # Test wrong study
    with pytest.raises(StudyNotFoundError):
        request_handler.export_study("WRONG")

    # Test good study
    assert b"Hello" == request_handler.export_study(name)
    exporter.export_file.assert_called_once_with(study_path)


@pytest.mark.unit_test
def test_export_compact_file(tmp_path: Path):
    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()

    exporter = Mock()
    exporter.export_compact.return_value = b"Hello"
    parser = Mock()
    parser.parse.return_value = 42

    request_handler = RequestHandler(
        study_parser=parser,
        url_engine=Mock(),
        exporter=exporter,
        path_studies=tmp_path,
        path_resources=Mock(),
        jsm_validator=Mock(),
    )

    assert b"Hello" == request_handler.export_study(name, compact=True)
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

    request_handler = request_handler_builder(path_studies=tmp_path)

    request_handler.url_engine.resolve.return_value = (None, None, None)

    request_handler.parse_folder = Mock()
    request_handler.parse_folder.return_value = {
        "study": {"antares": {"version": 700}}
    }

    filepath_zip = shutil.make_archive(study_path, "zip", study_path)
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

    request_handler = request_handler_builder(path_studies=tmp_path)
    request_handler.url_engine.resolve.return_value = (None, None, None)

    # Input
    url = "my-uuid/url/to/change"
    new = {"Hello": "World"}

    res = request_handler.edit_study(url, new)

    assert new == res
    request_handler.url_engine.resolve.assert_called_once_with(
        url="url/to/change", path=tmp_path / "my-uuid"
    )
    request_handler.study_parser.write(path=None, data=None, jsm=None)

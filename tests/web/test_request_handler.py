from pathlib import Path
from unittest.mock import Mock

import pytest

from api_iso_antares.web import RequestHandler
from api_iso_antares.web.request_handler import (
    RequestHandlerParameters,
    StudyNotFoundError,
)


@pytest.mark.unit_test
def test_get(tmp_path: str) -> None:

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

    data = {"toto": 42}
    expected_data = {"titi": 43}
    sub_route = "settings/blabla"

    study_reader_mock = Mock()
    study_reader_mock.parse.return_value = data

    url_engine_mock = Mock()
    url_engine_mock.apply.return_value = expected_data

    jsm_validator_mock = Mock()
    jsm_validator_mock.validate.return_value = None

    request_handler = RequestHandler(
        study_parser=study_reader_mock,
        url_engine=url_engine_mock,
        path_studies=path_to_studies,
        jsm_validator=jsm_validator_mock,
    )

    parameters = RequestHandlerParameters(depth=2)

    output = request_handler.get(
        route=f"study2.py/{sub_route}", parameters=parameters
    )

    assert output == expected_data

    study_reader_mock.parse.assert_called_once_with(
        path_to_studies / "study2.py"
    )
    jsm_validator_mock.validate.assert_called_once_with(data)
    url_engine_mock.apply.assert_called_once_with(
        Path(sub_route), data, parameters.depth
    )


@pytest.mark.unit_test
def test_assert_study_exist(tmp_path: str) -> None:
    # Create folders
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
        path_studies=path_to_studies,
        jsm_validator=Mock(),
    )
    request_handler._assert_study_exist(study_name)


@pytest.mark.unit_test
def test_assert_study_not_exist(tmp_path: str) -> None:
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
        path_studies=path_to_studies,
        jsm_validator=Mock(),
    )
    with pytest.raises(StudyNotFoundError):
        request_handler._assert_study_exist(study_name)


@pytest.mark.unit_test
def test_find_studies(tmp_path: str) -> None:
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
    request_handler = RequestHandler(
        study_parser=Mock(),
        url_engine=Mock(),
        path_studies=path_studies,
        jsm_validator=Mock(),
    )

    assert study_names == request_handler.get_studies()

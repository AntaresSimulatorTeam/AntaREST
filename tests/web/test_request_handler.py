from pathlib import Path
from unittest.mock import Mock

import pytest

from api_iso_antares.web import RequestHandler


@pytest.mark.unit_test
def test_get():
    data = {"toto": 42}
    expected_data = {"titi": 43}
    path_to_study = Path("path/to/study")
    route = "my_route"

    study_reader_mock = Mock()
    study_reader_mock.read.return_value = data

    url_engine_mock = Mock()
    url_engine_mock.apply.return_value = expected_data

    request_handler = RequestHandler(
        study_reader=study_reader_mock,
        url_engine=url_engine_mock,
        path_to_study=path_to_study,
    )

    output = request_handler.get(route=route)

    assert output == expected_data

    study_reader_mock.read.assert_called_once_with(path_to_study)
    study_reader_mock.validate.assert_called_once_with(data)
    url_engine_mock.apply.assert_called_once_with(route, data)


@pytest.mark.unit_test
def test_get_error_study_not_found():
    route = "/studies/WRONG_STUDY"

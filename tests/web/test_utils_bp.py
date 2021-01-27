import json
from http import HTTPStatus
from pathlib import Path
from unittest.mock import Mock

import pytest

from AntaREST.storage_api import __version__
from AntaREST.storage_api.web.server import create_server


@pytest.mark.unit_test
def test_version() -> None:

    mock_request_handler = Mock()
    mock_request_handler.path_resources = Path("/")

    app = create_server(mock_request_handler, res=Path())
    client = app.test_client()

    path = "/version"
    result = client.get(path)

    assert result.status_code == HTTPStatus.OK.value
    assert json.loads(result.data)["version"] == __version__

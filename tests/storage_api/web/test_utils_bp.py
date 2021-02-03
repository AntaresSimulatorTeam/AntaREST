import json
from http import HTTPStatus
from pathlib import Path
from unittest.mock import Mock

import pytest
from flask import Flask

from antarest import __version__
from antarest.common.config import Config
from antarest.storage_api.main import build_storage


@pytest.mark.unit_test
def test_version() -> None:

    mock_request_handler = Mock()
    mock_request_handler.path_resources = Path("/")

    app = Flask(__name__)
    build_storage(
        app, req=mock_request_handler, config=Config({"main": {"res": Path()}})
    )
    client = app.test_client()

    path = "/version"
    result = client.get(path)

    assert result.status_code == HTTPStatus.OK.value
    assert json.loads(result.data)["version"] == __version__

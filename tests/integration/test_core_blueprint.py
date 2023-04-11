from unittest import mock

from fastapi import FastAPI
from http import HTTPStatus
from starlette.testclient import TestClient


class TestVersionInfo:
    def test_version_info(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        res = client.get("/version")
        assert res.status_code == HTTPStatus.OK
        actual = res.json()
        expected = {
            "name": "AntaREST",
            "version": mock.ANY,
            "gitcommit": mock.ANY,
            "dependencies": {"Antares_Launcher": mock.ANY},
        }
        assert actual == expected

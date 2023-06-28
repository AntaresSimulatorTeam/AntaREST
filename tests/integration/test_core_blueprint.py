import http
import re
from unittest import mock

from fastapi import FastAPI
from starlette.testclient import TestClient


class RegEx:
    """A helper object that compares equal to a regex."""

    def __init__(self, regex):
        self.regex = regex
        self.match = re.compile(self.regex).fullmatch

    def __eq__(self, other):
        return isinstance(other, str) and self.match(other)

    def __ne__(self, other):
        return not isinstance(other, str) or not self.match(other)

    def __repr__(self):
        return f"<RegEx({self.regex!r})>"


class TestVersionInfo:
    def test_version_info(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        res = client.get("/version")
        res.raise_for_status()
        actual = res.json()
        expected = {
            "name": "AntaREST",
            "version": RegEx(r"\d+(?:\.\d+)+"),
            "gitcommit": RegEx(r"^[0-9a-fA-F]{40}$"),
            "dependencies": mock.ANY,
        }
        assert actual == expected


class TestKillWorker:
    def test_kill_worker__not_granted(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        res = client.get("/kill")
        assert res.status_code == http.HTTPStatus.UNAUTHORIZED, res.json()
        assert res.json() == {"detail": "Missing cookie access_token_cookie"}

    def test_kill_worker__nominal_case(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        # login as "admin"
        res = client.post(
            "/v1/login", json={"username": "admin", "password": "admin"}
        )
        res.raise_for_status()
        credentials = res.json()
        admin_access_token = credentials["access_token"]
        # kill the worker
        res = client.get(
            "/kill", headers={"Authorization": f"Bearer {admin_access_token}"}
        )
        assert res.status_code == 500, res.json()
        assert not res.content

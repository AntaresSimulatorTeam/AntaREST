import re
import subprocess
from unittest import mock

from fastapi import FastAPI
from http import HTTPStatus
from starlette.testclient import TestClient

from antarest.core import version_info
from antarest.core.version_info import get_dependencies, get_commit_id


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
            "dependencies": mock.ANY,
        }
        assert actual == expected

    def test_get_dependencies(self):
        dependencies = get_dependencies()
        assert isinstance(dependencies, dict)
        assert "fastapi" in dependencies
        assert re.compile(r"\d+\.\d+(?:\.\d+)?").match(dependencies["fastapi"])

    def test_get_commit_id(self, tmp_path):
        path_commit_id = tmp_path.joinpath("commit_id")
        with open(path_commit_id, "w") as f:
            f.write("fake_commit")
        assert get_commit_id(tmp_path) == "fake_commit"
        path_commit_id.unlink()
        assert (
            get_commit_id(tmp_path)
            == subprocess.check_output(
                "git log -1 HEAD --format=%H", encoding="utf-8", shell=True
            ).strip()
        )
        version_info.get_last_commit_from_git = mock.MagicMock(
            return_value="mock commit"
        )
        assert get_commit_id(tmp_path) == "mock commit"

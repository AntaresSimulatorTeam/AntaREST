import re
import subprocess
from pathlib import Path
from unittest import mock

from fastapi import FastAPI
from http import HTTPStatus
from starlette.testclient import TestClient

from antarest.core.version_info import get_dependencies, get_commit_id


class TestVersionInfo:
    antarest_path = Path(__file__).parent.parent.parent

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
        dict_dependencies = get_dependencies()
        pattern = re.compile(r"\d+\.\d+(?:\.\d+)?")
        requirements = (
            self.antarest_path.joinpath("requirements.txt")
            .read_text("utf-8")
            .split("\n")
        )
        print(requirements)
        dict_requirements = {}
        for requirement in requirements:
            key_value = requirement.split("=")
            key_value[0] = key_value[0].replace("~", "").replace("=", "")
            if len(key_value) >= 2 and key_value[0] != "AntaREST":
                dict_requirements[key_value[0]] = key_value[len(key_value) - 1]
        for key in dict_requirements:
            assert key.split("[")[0] in dict_dependencies
            assert pattern.match(dict_dependencies[key.split("[")[0]])

    def test_get_commit_id(self, git_repo):
        resources_path = self.antarest_path.joinpath("resources")
        path_commit_id = resources_path.joinpath("commit_id")
        with open(path_commit_id, "w") as f:
            f.write("fake_commit")
        assert get_commit_id(resources_path) == "fake_commit"
        path_commit_id.unlink()
        assert (
            get_commit_id(resources_path)
            == subprocess.check_output(
                "git log -1 HEAD --format=%H", encoding="utf-8", shell=True
            ).strip()
        )
        # Add a subprocess mock to complete the test
        # print(git_repo.run("git log -1 --HEAD --format=%H")) fails with the right Exception but not enough

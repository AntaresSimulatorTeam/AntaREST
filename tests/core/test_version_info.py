import re
from unittest.mock import patch

import pytest

from antarest.core.version_info import get_commit_id, get_dependencies


class TestVersionInfo:
    @pytest.mark.unit_test
    def test_get_dependencies(self) -> None:
        dependencies = get_dependencies()
        assert isinstance(dependencies, dict)
        # AntaREST is not a dependency of AntaREST
        assert "AntaREST" not in dependencies
        # lazy checking: we only check that FastAPI exist ;-)
        assert "fastapi" in dependencies
        assert all(
            # match at least one number. eg: "pywin32 == 306"
            re.fullmatch(r"\d+(?:\.\d+)*", ver)
            for ver in dependencies.values()
        )

    @pytest.mark.unit_test
    def test_get_commit_id__commit_id__exist(self, tmp_path) -> None:
        # fmt: off
        path_commit_id = tmp_path.joinpath("commit_id")
        path_commit_id.write_text("6d891aba6e4a1c3a6f43b8ca00b021a20d319091")
        assert (get_commit_id(tmp_path) == "6d891aba6e4a1c3a6f43b8ca00b021a20d319091")
        # fmt: on

    @pytest.mark.unit_test
    def test_get_commit_id__git_call_ok(self, tmp_path) -> None:
        actual = get_commit_id(tmp_path)
        assert re.fullmatch(r"[0-9a-fA-F]{40}", actual)

    @pytest.mark.unit_test
    def test_get_commit_id__git_call_failed(self, tmp_path) -> None:
        with patch("subprocess.check_output", side_effect=FileNotFoundError):
            assert not get_commit_id(tmp_path)

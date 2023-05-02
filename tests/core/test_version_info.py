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
            re.fullmatch(r"\d+(?:\.\d+)+", ver)
            for ver in dependencies.values()
        )

    @pytest.mark.unit_test
    def test_get_commit_id__commit_id__exist(self, tmp_path) -> None:
        path_commit_id = tmp_path.joinpath("commit_id")
        path_commit_id.write_text("fake_commit")
        assert get_commit_id(tmp_path) == "fake_commit"

    @pytest.mark.unit_test
    def test_get_commit_id__commit_id__missing(self, tmp_path) -> None:
        with patch(
            "antarest.core.version_info.get_last_commit_from_git",
            return_value="mock commit",
        ):
            assert get_commit_id(tmp_path) == "mock commit"

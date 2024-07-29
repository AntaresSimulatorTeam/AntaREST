from pathlib import Path

import pytest

from antarest.core.exceptions import StudyValidationError
from antarest.study.storage.study_upgrader import get_current_version


class TestGetCurrentVersion:
    @pytest.mark.parametrize(
        "version",
        [
            pytest.param("710"),
            pytest.param("  71"),
            pytest.param("  7.1   "),
            pytest.param(
                "",
                marks=pytest.mark.xfail(
                    reason="empty version",
                    raises=StudyValidationError,
                    strict=True,
                ),
            ),
        ],
    )
    def test_get_current_version(self, tmp_path: Path, version: str):
        # prepare the "study.antares" file
        study_antares_path = tmp_path.joinpath("study.antares")
        study_antares_path.write_text(f"version = {version}", encoding="utf-8")
        actual = get_current_version(tmp_path)
        assert actual == version.strip(), f"{actual=}"

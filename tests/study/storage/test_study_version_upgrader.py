from pathlib import Path

import pytest

from antarest.core.exceptions import StudyValidationError
from antarest.study.storage.study_upgrader import (
    InvalidUpgrade,
    UPGRADE_METHODS,
)
from antarest.study.storage.study_upgrader.study_version_upgrader import (
    can_upgrade_version,
    find_next_version,
    get_current_version,
)


class TestFindNextVersion:
    @pytest.mark.parametrize(
        "from_version, expected",
        [
            (UPGRADE_METHODS[0].old, UPGRADE_METHODS[0].new),
            (UPGRADE_METHODS[-1].old, UPGRADE_METHODS[-1].new),
            (UPGRADE_METHODS[-1].new, ""),
            ("3.14", ""),
        ],
    )
    def test_find_next_version(self, from_version: str, expected: str):
        actual = find_next_version(from_version)
        assert actual == expected


class TestCanUpgradeVersion:
    @pytest.mark.parametrize(
        "from_version, to_version",
        [
            pytest.param("700", "710"),
            pytest.param(
                "123",
                "123",
                marks=pytest.mark.xfail(
                    reason="same versions",
                    raises=InvalidUpgrade,
                    strict=True,
                ),
            ),
            pytest.param(
                "000",
                "123",
                marks=pytest.mark.xfail(
                    reason="version '000' not in 'old' versions",
                    raises=InvalidUpgrade,
                    strict=True,
                ),
            ),
            pytest.param(
                "700",
                "999",
                marks=pytest.mark.xfail(
                    reason="version '999' not in 'new' versions",
                    raises=InvalidUpgrade,
                    strict=True,
                ),
            ),
            pytest.param(
                "720",
                "710",
                marks=pytest.mark.xfail(
                    reason="versions inverted",
                    raises=InvalidUpgrade,
                    strict=True,
                ),
            ),
            pytest.param(
                800,
                "456",
                marks=pytest.mark.xfail(
                    reason="integer version 800 not in 'old' versions",
                    raises=InvalidUpgrade,
                    strict=True,
                ),
            ),
            pytest.param(
                "700",
                800,
                marks=pytest.mark.xfail(
                    reason="integer version 800 not in 'new' versions",
                    raises=InvalidUpgrade,
                    strict=True,
                ),
            ),
        ],
    )
    def test_can_upgrade_version(self, from_version: str, to_version: str):
        can_upgrade_version(from_version, to_version)


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

import logging
import re
import typing as t
from http import HTTPStatus
from http.client import HTTPException
from pathlib import Path

from antares.study.version import StudyVersion
from antares.study.version.upgrade_app import UpgradeApp

from antarest.core.exceptions import StudyValidationError

STUDY_ANTARES = "study.antares"
"""
Main file of an Antares study containing the caption, the version, the creation date, etc.
"""

logger = logging.getLogger(__name__)


class UpgradeMethod(t.NamedTuple):
    """Raw study upgrade method (old version, new version, upgrade function)."""

    old: str
    new: str


UPGRADE_METHODS = [
    UpgradeMethod("700", "710"),
    UpgradeMethod("710", "720"),
    UpgradeMethod("720", "800"),
    UpgradeMethod("800", "810"),
    UpgradeMethod("810", "820"),
    UpgradeMethod("820", "830"),
    UpgradeMethod("830", "840"),
    UpgradeMethod("840", "850"),
    UpgradeMethod("850", "860"),
    UpgradeMethod("860", "870"),
    UpgradeMethod("870", "880"),
]


class InvalidUpgrade(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


class StudyUpgrader:
    def __init__(self, study_path: Path, target_version: str):
        self.app = UpgradeApp(study_path, version=StudyVersion.parse(target_version))

    def upgrade(self) -> None:
        try:
            self.app()
        except Exception as e:
            raise InvalidUpgrade(str(e)) from e

    def get_upgrade_method(self) -> t.List[UpgradeMethod]:
        return self.app.upgrade_methods

    def should_denormalize(self) -> bool:
        return self.app.should_denormalize


def find_next_version(from_version: str) -> str:
    """
    Find the next study version from the given version.

    Args:
        from_version: The current version as a string.

    Returns:
        The next version as a string.
        If no next version was found, returns an empty string.
    """
    return next(
        (meth.new for meth in UPGRADE_METHODS if from_version == meth.old),
        "",
    )


def get_current_version(study_path: Path) -> str:
    """
    Get the current version of a study.

    Args:
        study_path: Path to the study.

    Returns:
        The current version of the study.

    Raises:
        StudyValidationError: If the version number is not found in the
        `study.antares` file or does not match the expected format.
    """

    antares_path = study_path / STUDY_ANTARES
    pattern = r"version\s*=\s*([\w.-]+)\s*"
    with antares_path.open(encoding="utf-8") as lines:
        for line in lines:
            if match := re.fullmatch(pattern, line):
                return match[1].rstrip()
    raise StudyValidationError(
        f"File parsing error: the version number is not found in '{antares_path}'"
        f" or does not match the expected '{pattern}' format."
    )

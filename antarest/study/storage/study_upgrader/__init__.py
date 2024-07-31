from http import HTTPStatus
from http.client import HTTPException
from pathlib import Path

from antares.study.version.model.study_version import StudyVersion
from antares.study.version.upgrade_app import UpgradeApp

from antarest.core.exceptions import UnsupportedStudyVersion


class InvalidUpgrade(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.UNPROCESSABLE_ENTITY, message)


class StudyUpgrader:
    def __init__(self, study_path: Path, target_version: str):
        try:
            version = StudyVersion.parse(target_version)
        except ValueError as e:
            raise InvalidUpgrade(str(e)) from e
        else:
            self.app = UpgradeApp(study_path, version=version)

    def upgrade(self) -> None:
        try:
            self.app()
        except Exception as e:
            raise InvalidUpgrade(str(e)) from e

    def should_denormalize_study(self) -> bool:
        try:
            return self.app.should_denormalize
        except Exception as e:
            raise InvalidUpgrade(str(e)) from e


def find_next_version(from_version: str) -> str:
    """
    Find the next study version from the given version.

    Args:
        from_version: The current version as a string.

    Returns:
        The next version as a string.

    Raises:
        UnsupportedStudyVersion if the current version is not supported or if the study is already in last version.
    """
    available_versions = ["700", "710", "720", "800", "810", "820", "830", "840", "850", "860", "870", "880"]
    for k, version in enumerate(available_versions):
        if version == from_version:
            if k == len(available_versions) - 1:
                raise UnsupportedStudyVersion(f"Your study is already in latest supported version: '{from_version}'")
            return available_versions[k + 1]
    raise UnsupportedStudyVersion(
        f"{from_version} is not a supported version, supported versions are: {available_versions}"
    )

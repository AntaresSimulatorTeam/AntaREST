import datetime
from pathlib import Path
from typing import IO, Tuple
from uuid import uuid4
from zipfile import ZipFile, BadZipFile

from markupsafe import escape

from antarest.common.custom_types import JSON
from antarest.storage.model import Study
from antarest.storage.web.exceptions import (
    StudyValidationError,
    BadZipBinary,
    IncorrectPathError,
)


class StorageServiceUtils:
    """
    Useful study tools.

    """

    @staticmethod
    def check_antares_version(study: JSON) -> None:
        """
        Check if study version is higher or equels to v7
        Args:
            study: study

        Returns: none or raise error if incorrect version

        """

        version = study["study"]["antares"]["version"]
        major_version = int(version / 100)

        if major_version < 7:
            raise StudyValidationError(
                "The API do not handle study with antares version inferior to 7"
            )

    @staticmethod
    def generate_uuid() -> str:
        """
        Generate a random study id
        Returns: uuid

        """
        return str(uuid4())

    @staticmethod
    def sanitize(uuid: str) -> str:
        """
        Sanitize uuid
        Args:
            uuid: study id

        Returns: sanitize id

        """
        return str(escape(uuid))

    @staticmethod
    def extract_zip(stream: IO[bytes], dst: Path) -> None:
        """
        Extract zip archive
        Args:
            stream: zip file
            dst: destination path

        Returns:

        """
        try:
            with ZipFile(stream) as zip_output:
                zip_output.extractall(path=dst)
        except BadZipFile:
            raise BadZipBinary("Only zip file are allowed.")

    @staticmethod
    def assert_path_can_be_matrix(path: Path) -> None:
        """
        assert if path point to a matrix
        Args:
            path: path to file

        Returns: raise error if not matrix

        """
        if path.suffix != ".txt":
            raise IncorrectPathError(
                f"{path} is not a valid path for a matrix (use txt extension)."
            )

    @staticmethod
    def update_antares_info(metadata: Study, study_data: JSON) -> None:
        """
        Update study.antares data
        Args:
            metadata: study information
            study_data: study data formatted in json

        Returns: none, update is directly apply on study_data

        """
        info_antares = study_data["study"]["antares"]

        info_antares["caption"] = metadata.name
        info_antares["created"] = int(metadata.created_at.timestamp())
        info_antares["lastsave"] = int(metadata.updated_at.timestamp())

    @staticmethod
    def extract_info_from_url(route: str) -> Tuple[str, str]:
        """
        Separate study uuid from data path
        Args:
            route: url

        Returns: (study, uuid, path inside study)

        """
        route_parts = route.split("/")
        uuid = route_parts[0]
        url = "/".join(route_parts[1:])

        return uuid, url

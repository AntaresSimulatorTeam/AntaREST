import re
import time
from pathlib import Path
from typing import IO, Tuple
from uuid import uuid4
from zipfile import ZipFile, BadZipFile

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

        version = study["study"]["antares"]["version"]
        major_version = int(version / 100)

        if major_version < 7:
            raise StudyValidationError(
                "The API do not handle study with antares version inferior to 7"
            )

    @staticmethod
    def generate_uuid() -> str:
        return str(uuid4())

    @staticmethod
    def sanitize(uuid: str) -> str:
        return re.sub(r"[^0-9-]", "_", uuid)

    @staticmethod
    def extract_zip(stream: IO[bytes], dst: Path) -> None:
        try:
            with ZipFile(stream) as zip_output:
                zip_output.extractall(path=dst)
        except BadZipFile:
            raise BadZipBinary("Only zip file are allowed.")

    @staticmethod
    def assert_path_can_be_matrix(path: Path) -> None:
        if path.suffix != ".txt":
            raise IncorrectPathError(
                f"{path} is not a valid path for a matrix (use txt extension)."
            )

    @staticmethod
    def update_antares_info(metadata: Study, study_data: JSON) -> None:
        info_antares = study_data["study"]["antares"]

        info_antares["caption"] = metadata.name
        info_antares["created"] = metadata.created_at
        info_antares["lastsave"] = metadata.updated_at

    @staticmethod
    def extract_info_from_url(route: str) -> Tuple[str, str]:
        route_parts = route.split("/")
        uuid = route_parts[0]
        url = "/".join(route_parts[1:])

        return uuid, url

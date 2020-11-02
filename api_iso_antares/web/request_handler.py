from pathlib import Path
from typing import Any

from api_iso_antares.antares_io.validator import JsmValidator
from api_iso_antares.custom_exceptions import HtmlException
from api_iso_antares.custom_types import JSON
from api_iso_antares.engine import UrlEngine
from api_iso_antares.engine.filesystem.engine import (
    FileSystemEngine,
)
from api_iso_antares.jsm import JsonSchema


class StudyNotFoundError(HtmlException):
    def __init__(self, message: str):
        super(StudyNotFoundError, self).__init__(message, 404)


class RequestHandlerParameters:
    def __init__(self, depth: int = 3) -> None:
        self.depth = depth

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, type(self)) and self.__dict__ == other.__dict__
        )

    def __str__(self) -> str:
        return "{}({})".format(
            type(self).__name__,
            ", ".join(
                [
                    "{}={} ({})".format(
                        k, str(self.__dict__[k]), type(self.__dict__[k])
                    )
                    for k in sorted(self.__dict__)
                ]
            ),
        )

    def __repr__(self) -> str:
        return self.__str__()


class RequestHandler:
    def __init__(
        self,
        study_parser: FileSystemEngine,
        url_engine: UrlEngine,
        path_studies: Path,
        jsm_validator: JsmValidator,
    ):
        self.study_reader = study_parser
        self.url_engine = url_engine
        self.path_to_studies = path_studies
        self.jsm_validator = jsm_validator

    def get(self, route: str, parameters: RequestHandlerParameters) -> Any:
        path_route = Path(route)
        study_name = path_route.parts[0]
        self._assert_study_exist(study_name)

        data = self.study_reader.parse(self.path_to_studies / study_name)
        self.jsm_validator.validate(data)

        route_cut = path_route.relative_to(Path(study_name))
        return self.url_engine.apply(route_cut, data, parameters.depth)

    def _assert_study_exist(self, study_name: str) -> None:
        dirs_files = self.path_to_studies.glob(pattern="*")
        dirs = [str(folder.name) for folder in dirs_files if folder.is_dir()]
        if study_name not in dirs:
            raise StudyNotFoundError(f"{study_name} not found")

    def get_studies(self) -> JSON:
        studies = {"studies": []}
        studies_list = []

        for path in self.path_to_studies.rglob("*"):
            if path.name == "study.antares" and path.is_file():
                studies_list.append(path.parent.name)

        studies["studies"] = sorted(studies_list)

        return studies

    def get_jsm(self) -> JsonSchema:
        return self.jsm_validator.jsm

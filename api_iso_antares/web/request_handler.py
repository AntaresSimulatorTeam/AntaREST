import copy
import time
from pathlib import Path
from typing import Any, List
from http import HTTPStatus
from zipfile import ZipFile

from api_iso_antares.antares_io.validator import JsmValidator
from api_iso_antares.custom_exceptions import HtmlException
from api_iso_antares.custom_types import JSON
from api_iso_antares.engine import UrlEngine
from api_iso_antares.engine.filesystem.engine import (
    FileSystemEngine,
)
from api_iso_antares.jsm import JsonSchema


class StudyNotFoundError(HtmlException):
    def __init__(self, message: str) -> None:
        super().__init__(message, 404)


class StudyAlreadyExistError(HtmlException):
    def __init__(self) -> None:
        super().__init__(
            "A study already exists with this name.", HTTPStatus.CONFLICT
        )


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
        path_resources: Path,
        jsm_validator: JsmValidator,
    ):
        self.study_parser = study_parser
        self.url_engine = url_engine
        self.path_to_studies = path_studies
        self.path_resources = path_resources
        self.jsm_validator = jsm_validator

    def get(self, route: str, parameters: RequestHandlerParameters) -> Any:
        path_route = Path(route)
        study_name = path_route.parts[0]
        self._assert_study_exist(study_name)

        study_data = self.parse_study(study_name)

        route_cut = path_route.relative_to(Path(study_name))
        return self.url_engine.apply(route_cut, study_data, parameters.depth)

    def parse_study(self, name: str) -> JSON:
        study_path = self.get_study_path(name)
        data = self.study_parser.parse(study_path)
        self.jsm_validator.validate(data)
        return data

    def _assert_study_exist(self, study_name: str) -> None:
        if not self.is_study_exist(study_name):
            raise StudyNotFoundError(f"{study_name} not found")

    def _assert_study_not_exist(self, study_name: str) -> None:
        if self.is_study_exist(study_name):
            raise StudyAlreadyExistError

    def is_study_exist(self, study_name: str) -> bool:
        return study_name in self.get_study_names()

    def get_study_names(self) -> List[str]:
        studies_list = []
        for path in self.path_to_studies.iterdir():
            if (path / "study.antares").is_file():
                studies_list.append(path.name)
        return sorted(studies_list)

    def get_studies_informations(self) -> JSON:
        studies = {}
        study_names = self.get_study_names()
        for name in study_names:
            studies[name] = self.get_study_informations(name)
        return studies

    def get_study_informations(self, study_name: str) -> JSON:
        url = study_name + "/study"
        return self.get(url, RequestHandlerParameters(depth=2))

    def get_jsm(self) -> JsonSchema:
        return self.jsm_validator.jsm

    def get_study_path(self, name: str) -> Path:
        return self.path_to_studies / name

    def create_study(self, name: str) -> None:

        self._assert_study_not_exist(name)

        empty_study_zip = self.path_resources / "empty-study.zip"

        path_study = self.get_study_path(name)
        path_study.mkdir()

        with ZipFile(empty_study_zip) as zip_output:
            zip_output.extractall(path=path_study)

        study_data = self.parse_study(name)
        RequestHandler._update_antares_info(name, study_data)
        self.study_parser.write(path_study, study_data)

    def copy_study(self, src: str, dest: str) -> None:

        self._assert_study_exist(src)
        self._assert_study_not_exist(dest)

        path_source = self.get_study_path(src)
        data_source = self.study_parser.parse(path_source)

        path_destination = self.get_study_path(dest)
        data_destination = copy.deepcopy(data_source)

        RequestHandler._update_antares_info(dest, data_destination)
        data_destination["output"] = None

        self.study_parser.write(path_destination, data_destination)

    @staticmethod
    def _update_antares_info(study_name: str, study_data: JSON) -> None:

        info_antares = study_data["study"]["antares"]

        info_antares["caption"] = study_name
        current_time = int(time.time())
        info_antares["created"] = current_time
        info_antares["lastsave"] = current_time

import time
from pathlib import Path
from typing import Any, List
from http import HTTPStatus
from zipfile import ZipFile

import api_iso_antares
from api_iso_antares.antares_io.validator import JsmValidator
from api_iso_antares.custom_exceptions import HtmlException
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
        jsm_validator: JsmValidator,
    ):
        self.study_parser = study_parser
        self.url_engine = url_engine
        self.path_to_studies = path_studies
        self.jsm_validator = jsm_validator

    def get(self, route: str, parameters: RequestHandlerParameters) -> Any:
        path_route = Path(route)
        study_name = path_route.parts[0]
        self._assert_study_exist(study_name)

        data = self.study_parser.parse(self.path_to_studies / study_name)
        self.jsm_validator.validate(data)

        route_cut = path_route.relative_to(Path(study_name))
        return self.url_engine.apply(route_cut, data, parameters.depth)

    def _assert_study_exist(self, study_name: str) -> None:
        if not self.is_study_exist(study_name):
            raise StudyNotFoundError(f"{study_name} not found")

    def _assert_study_not_exist(self, study_name: str) -> None:
        if self.is_study_exist(study_name):
            raise StudyAlreadyExistError

    def is_study_exist(self, study_name: str) -> bool:
        return study_name in self.get_studies()

    def get_studies(self) -> List[str]:
        studies_list = []
        for path in self.path_to_studies.iterdir():
            if (path / "study.antares").is_file():
                studies_list.append(path.name)
        return sorted(studies_list)

    def get_jsm(self) -> JsonSchema:
        return self.jsm_validator.jsm

    def create_study(self, name: str) -> None:

        self._assert_study_not_exist(name)

        root_package = api_iso_antares.ROOT_DIR
        empty_study_zip = root_package / "resources/empty-study.zip"

        path_study = self.path_to_studies / name
        path_study.mkdir()

        with ZipFile(empty_study_zip) as zip_output:
            zip_output.extractall(path=path_study)

        self._update_antares_info(path_study)

    def _update_antares_info(self, path_study: Path) -> None:

        path_study_antares_infos = path_study / "study.antares"

        reader = self.study_parser.get_reader()
        data = reader.read(path_study_antares_infos)
        data["antares"]["caption"] = path_study.name
        current_time = int(time.time())
        data["antares"]["created"] = current_time
        data["antares"]["lastsave"] = current_time

        writer = self.study_parser.get_writer()
        writer.write(data, path_study_antares_infos)

    def copy_study(self, src: str, dest: str) -> None:
        pass

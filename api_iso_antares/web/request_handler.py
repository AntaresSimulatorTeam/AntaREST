import copy
import json
import os
import shutil
import time
from io import BytesIO
from pathlib import Path
from typing import Any, IO, List, Tuple
from uuid import uuid4
from zipfile import BadZipFile, ZipFile

from api_iso_antares.antares_io.exporter.export_file import Exporter
from api_iso_antares.custom_types import JSON, SUB_JSON
from api_iso_antares.filesystem.factory import StudyFactory
from api_iso_antares.web.html_exception import (
    BadZipBinary,
    IncorrectPathError,
    StudyAlreadyExistError,
    StudyNotFoundError,
    StudyValidationError,
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
        study_factory: StudyFactory,
        exporter: Exporter,
        path_studies: Path,
        path_resources: Path,
    ):
        self.study_factory = study_factory
        self.exporter = exporter
        self.path_to_studies = path_studies
        self.path_resources = path_resources

    def get(self, route: str, parameters: RequestHandlerParameters) -> JSON:
        uuid, url, study_path = self._extract_info_from_url(route)
        self.assert_study_exist(uuid)

        _, study = self.study_factory.create_from_fs(study_path)
        parts = [item for item in url.split("/") if item]

        data = study.get(parts, depth=parameters.depth)
        del study
        return data

    def assert_study_exist(self, uuid: str) -> None:
        if not self.is_study_existing(uuid):
            raise StudyNotFoundError(
                f"Study with the uuid {uuid} does not exist."
            )

    def assert_study_not_exist(self, uuid: str) -> None:
        if self.is_study_existing(uuid):
            raise StudyAlreadyExistError(
                f"A study already exist with the uuid {uuid}."
            )

    def is_study_existing(self, uuid: str) -> bool:
        return uuid in self.get_study_uuids()

    def get_study_uuids(self) -> List[str]:
        studies_list = []
        for path in self.path_to_studies.iterdir():
            if (path / "study.antares").is_file():
                studies_list.append(path.name)

        # sorting needed for test
        return sorted(studies_list)

    def get_studies_informations(self) -> JSON:
        studies = {}
        study_uuids = self.get_study_uuids()
        for uuid in study_uuids:
            studies[uuid] = self.get_study_informations(uuid)
        return studies

    def get_study_informations(self, uuid: str) -> SUB_JSON:
        url = uuid + "/study"
        return self.get(url, RequestHandlerParameters(depth=2))

    def get_study_path(self, uuid: str) -> Path:
        return self.path_to_studies / uuid

    def create_study(self, study_name: str) -> str:

        empty_study_zip = self.path_resources / "empty-study.zip"

        uuid = RequestHandler.generate_uuid()

        path_study = self.get_study_path(uuid)
        path_study.mkdir()

        with ZipFile(empty_study_zip) as zip_output:
            zip_output.extractall(path=path_study)

        study_data = self.get(
            uuid, parameters=RequestHandlerParameters(depth=10)
        )
        RequestHandler._update_antares_info(study_name, study_data)

        _, study = self.study_factory.create_from_fs(path_study)
        study.save(study_data)

        return uuid

    def copy_study(self, src_uuid: str, dest_study_name: str) -> str:

        uuid, url, study_path = self._extract_info_from_url(src_uuid)
        self.assert_study_exist(uuid)

        config, study = self.study_factory.create_from_fs(study_path)
        data_source = study.get()
        del study

        uuid = RequestHandler.generate_uuid()
        config.path = self.get_study_path(uuid)
        data_destination = copy.deepcopy(data_source)

        RequestHandler._update_antares_info(dest_study_name, data_destination)
        if "output" in data_destination:
            del data_destination["output"]
        config.outputs = {}

        study = self.study_factory.create_from_config(config)
        study.save(data_destination)
        del study
        return uuid

    def export_study(
        self, name: str, compact: bool = False, outputs: bool = True
    ) -> BytesIO:
        path_study = self.path_to_studies / name

        self.assert_study_exist(name)

        if compact:
            config, study = self.study_factory.create_from_fs(
                path=self.path_to_studies / name
            )

            if not outputs:
                config.outputs = dict()
                study = self.study_factory.create_from_config(config)

            data = study.get()
            del study
            return self.exporter.export_compact(path_study, data)
        else:
            return self.exporter.export_file(path_study, outputs)

    def delete_study(self, name: str) -> None:
        self.assert_study_exist(name)
        study_path = self.get_study_path(name)
        shutil.rmtree(study_path)

    def upload_matrix(self, path: str, data: bytes) -> None:

        relative_path_matrix = Path(path)
        uuid = relative_path_matrix.parts[0]

        self.assert_study_exist(uuid)
        RequestHandler.assert_path_can_be_matrix(relative_path_matrix)

        path_matrix = self.path_to_studies / relative_path_matrix

        path_matrix.write_bytes(data)

    def import_study(self, stream: IO[bytes]) -> str:

        uuid = RequestHandler.generate_uuid()
        path_study = Path(self.path_to_studies) / uuid
        path_study.mkdir()
        RequestHandler.extract_zip(stream, path_study)

        data_file = path_study / "data.json"
        if data_file.is_file() and (path_study / "res").is_dir():
            with open(data_file) as file:
                data = json.load(file)
                _, study = self.study_factory.create_from_json(
                    path_study, data
                )
                study.save(data)
            del study
            shutil.rmtree(path_study / "res")
            os.remove(str(data_file.absolute()))

        data = self.get(uuid, parameters=RequestHandlerParameters(depth=-1))
        if data is None:
            self.delete_study(uuid)
            return ""  # TODO return exception

        return uuid

    def edit_study(self, route: str, new: JSON) -> JSON:
        # Get data
        uuid, url, study_path = self._extract_info_from_url(route)
        self.assert_study_exist(uuid)

        _, study = self.study_factory.create_from_fs(study_path)
        study.save(new, url.split("/"))
        del study
        return new

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
    def _update_antares_info(study_name: str, study_data: JSON) -> None:
        # TODO return value rather than change implicitly
        info_antares = study_data["study"]["antares"]

        info_antares["caption"] = study_name
        current_time = int(time.time())
        info_antares["created"] = current_time
        info_antares["lastsave"] = current_time

    def _extract_info_from_url(self, route: str) -> Tuple[str, str, Path]:
        route_parts = route.split("/")
        uuid = route_parts[0]
        url = "/".join(route_parts[1:])
        study_path = self.path_to_studies / uuid

        return uuid, url, study_path

import copy
import shutil
import tempfile
import time
from io import BytesIO
from pathlib import Path
from typing import Any, IO, List
from uuid import uuid4
from zipfile import BadZipFile, ZipFile

from api_iso_antares.antares_io.exporter.export_file import Exporter
from api_iso_antares.antares_io.validator import JsmValidator
from api_iso_antares.web.html_exception import (
    BadZipBinary,
    IncorrectPathError,
    StudyAlreadyExistError,
    StudyNotFoundError,
    StudyValidationError,
    UrlNotMatchJsonDataError,
)
from api_iso_antares.custom_types import JSON, SUB_JSON
from api_iso_antares.engine import UrlEngine
from api_iso_antares.engine.filesystem.engine import (
    FileSystemEngine,
)
from api_iso_antares.jsm import JsonSchema


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
        exporter: Exporter,
        path_studies: Path,
        path_resources: Path,
        jsm_validator: JsmValidator,
    ):
        self.study_parser = study_parser
        self.url_engine = url_engine
        self.exporter = exporter
        self.path_to_studies = path_studies
        self.path_resources = path_resources
        self.jsm_validator = jsm_validator

    def get(
        self, route: str, parameters: RequestHandlerParameters
    ) -> SUB_JSON:
        path_route = Path(route)
        uuid = path_route.parts[0]
        self.assert_study_exist(uuid)

        study_data = self.parse_study(uuid)

        route_cut = path_route.relative_to(Path(uuid))

        data = self.get_data(parameters, route_cut, study_data)

        return data

    def get_data(
        self,
        parameters: RequestHandlerParameters,
        route_cut: Path,
        study_data: JSON,
    ) -> SUB_JSON:
        try:
            data = self.url_engine.apply(
                route_cut, study_data, parameters.depth
            )
        except KeyError:
            raise UrlNotMatchJsonDataError(
                f"Key {route_cut} not in the study."
            )
        return data

    def parse_study(self, uuid: str, do_validate: bool = True) -> JSON:
        study_path = self.get_study_path(uuid)
        return self.parse_folder(study_path, do_validate)

    def parse_folder(self, path: Path, do_validate: bool = True) -> JSON:
        data = self.study_parser.parse(path)
        if do_validate:
            try:
                self.jsm_validator.validate(data)
            except Exception as e:
                raise StudyValidationError(str(e))
        return data

    def assert_study_exist(self, uuid: str) -> None:
        if not self.is_study_exist(uuid):
            raise StudyNotFoundError(
                f"Study with the uuid {uuid} does not exist."
            )

    def assert_study_not_exist(self, uuid: str) -> None:
        if self.is_study_exist(uuid):
            raise StudyAlreadyExistError(
                f"A study already exist with the uuid {uuid}."
            )

    def is_study_exist(self, uuid: str) -> bool:
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

    def get_jsm(self) -> JsonSchema:
        return self.jsm_validator.jsm

    def get_study_path(self, uuid: str) -> Path:
        return self.path_to_studies / uuid

    def create_study(self, study_name: str) -> str:

        empty_study_zip = self.path_resources / "empty-study.zip"

        uuid = RequestHandler.generate_uuid()

        path_study = self.get_study_path(uuid)
        path_study.mkdir()

        with ZipFile(empty_study_zip) as zip_output:
            zip_output.extractall(path=path_study)

        study_data = self.parse_study(uuid, do_validate=False)
        RequestHandler._update_antares_info(study_name, study_data)
        self.study_parser.write(path_study, study_data)

        return uuid

    def copy_study(self, src_uuid: str, dest_study_name: str) -> str:

        self.assert_study_exist(src_uuid)

        path_source = self.get_study_path(src_uuid)
        data_source = self.study_parser.parse(path_source)

        uuid = RequestHandler.generate_uuid()
        path_destination = self.get_study_path(uuid)
        data_destination = copy.deepcopy(data_source)

        RequestHandler._update_antares_info(dest_study_name, data_destination)
        data_destination["output"] = None

        self.study_parser.write(path_destination, data_destination)

        return uuid

    def export_study(self, name: str, compact: bool = False) -> BytesIO:
        path_study = self.path_to_studies / name

        self.assert_study_exist(name)

        if compact:
            data = self.study_parser.parse(self.path_to_studies / name)
            self.jsm_validator.validate(data)
            return self.exporter.export_compact(path_study, data)
        else:
            return self.exporter.export_file(path_study)

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

        with tempfile.TemporaryDirectory() as tmp_directory:

            tmp_path_study = Path(tmp_directory) / uuid
            tmp_path_study.mkdir()

            RequestHandler.extract_zip(stream, tmp_path_study)

            study = self.parse_folder(tmp_path_study)
            RequestHandler.check_antares_version(study)

            shutil.move(str(tmp_path_study), str(self.path_to_studies))

        return uuid

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

        info_antares = study_data["study"]["antares"]

        info_antares["caption"] = study_name
        current_time = int(time.time())
        info_antares["created"] = current_time
        info_antares["lastsave"] = current_time

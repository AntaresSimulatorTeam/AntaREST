import copy
import json
import os
import shutil
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List, IO, Tuple, Any
from uuid import uuid4
from zipfile import ZipFile, BadZipFile

from antarest.common.config import Config
from antarest.common.custom_types import JSON
from antarest.storage.repository.antares_io.exporter.export_file import (
    Exporter,
)
from antarest.storage.repository.antares_io.reader import IniReader
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.factory import StudyFactory
from antarest.storage.web.exceptions import (
    StudyNotFoundError,
    StudyAlreadyExistError,
    BadOutputError,
    IncorrectPathError,
    BadZipBinary,
    StudyValidationError,
)


class StorageServiceParameters:
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


class StorageService:
    def __init__(
        self, study_factory: StudyFactory, exporter: Exporter, config: Config
    ):
        self.study_factory = study_factory
        self.exporter = exporter
        self.path_to_studies = Path(config["storage.studies"])
        self.path_resources = Path(config["main.res"])

    def get(self, route: str, parameters: StorageServiceParameters) -> JSON:
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
        studies_list = [
            path.name
            for path in self.path_to_studies.iterdir()
            if (path / "study.antares").is_file()
        ]

        # sorting needed for test
        return sorted(studies_list)

    def get_studies_information(self) -> JSON:
        return {
            uuid: self.get_study_information(uuid)
            for uuid in self.get_study_uuids()
        }

    def get_study_information(self, uuid: str) -> JSON:
        config = StudyConfig(study_path=self.path_to_studies / uuid)
        study = self.study_factory.create_from_config(config)
        return study.get(url=["study"])

    def get_study_path(self, uuid: str) -> Path:
        return self.path_to_studies / uuid

    def create_study(self, study_name: str) -> str:

        empty_study_zip = self.path_resources / "empty-study.zip"

        uuid = StorageService.generate_uuid()

        path_study = self.get_study_path(uuid)
        path_study.mkdir()

        with ZipFile(empty_study_zip) as zip_output:
            zip_output.extractall(path=path_study)

        study_data = self.get(
            uuid, parameters=StorageServiceParameters(depth=10)
        )
        StorageService._update_antares_info(study_name, study_data)

        _, study = self.study_factory.create_from_fs(path_study)
        study.save(study_data)

        return uuid

    def copy_study(self, src_uuid: str, dest_study_name: str) -> str:

        uuid, url, study_path = self._extract_info_from_url(src_uuid)
        self.assert_study_exist(uuid)

        config, study = self.study_factory.create_from_fs(study_path)
        data_source = study.get()
        del study

        uuid = StorageService.generate_uuid()
        config.path = self.get_study_path(uuid)
        data_destination = copy.deepcopy(data_source)

        StorageService._update_antares_info(dest_study_name, data_destination)
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

    def delete_output(self, uuid: str, output_name: str) -> None:
        output_path = self.path_to_studies / uuid / "output" / output_name
        shutil.rmtree(output_path, ignore_errors=True)

    def upload_matrix(self, path: str, data: bytes) -> None:

        relative_path_matrix = Path(path)
        uuid = relative_path_matrix.parts[0]

        self.assert_study_exist(uuid)
        StorageService.assert_path_can_be_matrix(relative_path_matrix)

        path_matrix = self.path_to_studies / relative_path_matrix

        path_matrix.write_bytes(data)

    def import_study(self, stream: IO[bytes]) -> str:
        uuid = StorageService.generate_uuid()
        path_study = Path(self.path_to_studies) / uuid
        path_study.mkdir()
        StorageService.extract_zip(stream, path_study)

        data_file = path_study / "data.json"

        # If compact study generate tree and launch save with data.json
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

        data = self.get(uuid, parameters=StorageServiceParameters(depth=-1))
        if data is None:
            self.delete_study(uuid)
            return ""  # TODO return exception

        return uuid

    def import_output(self, uuid: str, stream: IO[bytes]) -> JSON:
        path_output = (
            Path(self.path_to_studies) / uuid / "output" / "imported_output"
        )
        path_output.mkdir()
        StorageService.extract_zip(stream, path_output)

        ini_reader = IniReader()
        info_antares_output = ini_reader.read(
            path_output / "info.antares-output"
        )["general"]

        date = datetime.fromtimestamp(
            int(info_antares_output["timestamp"])
        ).strftime("%Y%m%d-%H%M")

        mode = "eco" if info_antares_output["mode"] == "Economy" else "adq"
        name = (
            f"-{info_antares_output['name']}"
            if info_antares_output["name"]
            else ""
        )

        output_name = f"{date}{mode}{name}"
        path_output.rename(Path(path_output.parent, output_name))

        output_id = (
            sorted(os.listdir(path_output.parent)).index(output_name) + 1
        )

        data = self.get(
            f"{uuid}/output/{output_id}",
            parameters=StorageServiceParameters(depth=-1),
        )

        if data is None:
            self.delete_output(uuid, "imported_output")
            raise BadOutputError("The output provided is not conform.")

        return data

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

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import IO

from antarest.common.custom_types import JSON
from antarest.storage.business.storage_service_utils import StorageServiceUtils
from antarest.storage.business.study_service import StudyService
from antarest.storage.repository.antares_io.reader import IniReader
from antarest.storage.repository.filesystem.factory import StudyFactory
from antarest.storage.business.storage_service_parameters import (
    StorageServiceParameters,
)
from antarest.storage.web.exceptions import BadOutputError


class ImporterService:
    def __init__(
        self,
        path_to_studies: Path,
        study_service: StudyService,
        study_factory: StudyFactory,
    ):
        self.study_service = study_service
        self.path_to_studies = path_to_studies
        self.study_factory = study_factory

    def upload_matrix(self, path: str, data: bytes) -> None:

        relative_path_matrix = Path(path)
        uuid = relative_path_matrix.parts[0]

        self.study_service.check_study_exist(uuid)
        StorageServiceUtils.assert_path_can_be_matrix(relative_path_matrix)

        path_matrix = self.path_to_studies / relative_path_matrix

        path_matrix.write_bytes(data)

    def import_study(self, stream: IO[bytes]) -> str:
        uuid = StorageServiceUtils.generate_uuid()
        path_study = Path(self.path_to_studies) / uuid
        path_study.mkdir()
        StorageServiceUtils.extract_zip(stream, path_study)

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

        data = self.study_service.get(
            uuid, parameters=StorageServiceParameters(depth=-1)
        )
        if data is None:
            self.study_service.delete_study(uuid)
            return ""  # TODO return exception

        return uuid

    def import_output(self, uuid: str, stream: IO[bytes]) -> JSON:
        path_output = (
            Path(self.path_to_studies) / uuid / "output" / "imported_output"
        )
        path_output.mkdir()
        StorageServiceUtils.extract_zip(stream, path_output)

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

        data = self.study_service.get(
            f"{uuid}/output/{output_id}",
            parameters=StorageServiceParameters(depth=-1),
        )

        if data is None:
            self.study_service.delete_output(uuid, "imported_output")
            raise BadOutputError("The output provided is not conform.")

        return data

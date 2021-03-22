import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import IO
from uuid import uuid4

from antarest.common.config import Config
from antarest.common.custom_types import JSON
from antarest.common.interfaces.eventbus import IEventBus
from antarest.storage.business.storage_service_utils import StorageServiceUtils
from antarest.storage.business.study_service import StudyService
from antarest.storage.model import Metadata
from antarest.storage.repository.antares_io.reader import IniReader
from antarest.storage.repository.filesystem.factory import StudyFactory
from antarest.storage.web.exceptions import (
    BadOutputError,
    StudyValidationError,
)

logger = logging.getLogger(__name__)


class ImporterService:
    def __init__(
        self,
        study_service: StudyService,
        study_factory: StudyFactory,
    ):
        self.study_service = study_service
        self.study_factory = study_factory

    def upload_matrix(
        self, metadata: Metadata, path: str, data: bytes
    ) -> None:

        relative_path_matrix = Path(path)

        self.study_service.check_study_exists(metadata)
        StorageServiceUtils.assert_path_can_be_matrix(relative_path_matrix)

        path_matrix = (
            self.study_service.get_workspace_path(metadata.workspace)
            / relative_path_matrix
        )

        path_matrix.write_bytes(data)

    def import_study(self, metadata: Metadata, stream: IO[bytes]) -> Metadata:
        path_study = self.study_service.get_study_path(metadata)
        path_study.mkdir()

        try:
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
            else:
                fix_study_root(path_study)

            data = self.study_service.get(metadata, url="", depth=-1)
            if data is None:
                self.study_service.delete_study(metadata)
                raise StudyValidationError("Fail to import study")
        except Exception as e:
            shutil.rmtree(path_study)
            raise e

        metadata.path = str(path_study)
        return metadata

    def import_output(self, metadata: Metadata, stream: IO[bytes]) -> JSON:
        path_output = (
            self.study_service.get_study_path(metadata)
            / "output"
            / "imported_output"
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
            metadata,
            f"output/{output_id}",
            -1,
        )

        if data is None:
            self.study_service.delete_output(metadata, "imported_output")
            raise BadOutputError("The output provided is not conform.")

        return data


def fix_study_root(study_path: Path) -> None:
    """
    Fix possibly the wrong study root on zipped archive (when the study root is nested)

    @param study_path the study initial root path
    """
    if not study_path.is_dir():
        raise StudyValidationError("Not a directory")

    root_path = study_path
    contents = os.listdir(root_path)
    sub_root_path = None
    while len(contents) == 1 and (root_path / contents[0]).is_dir():
        new_root = root_path / contents[0]
        if sub_root_path is None:
            sub_root_path = root_path / str(uuid4())
            shutil.move(str(new_root), str(sub_root_path))
            new_root = sub_root_path

        logger.debug(f"Searching study root in {new_root}")
        root_path = new_root
        if not new_root.is_dir():
            raise StudyValidationError("Not a directory")
        contents = os.listdir(new_root)

    if sub_root_path is not None:
        for item in os.listdir(root_path):
            shutil.move(str(root_path / item), str(study_path))
        shutil.rmtree(sub_root_path)

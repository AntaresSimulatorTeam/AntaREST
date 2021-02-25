import copy
import shutil
from pathlib import Path
from typing import List, Tuple
from zipfile import ZipFile

from antarest.common.custom_types import JSON
from antarest.storage.business.storage_service_utils import StorageServiceUtils
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.factory import StudyFactory
from antarest.storage.business.storage_service_parameters import (
    StorageServiceParameters,
)
from antarest.storage.web.exceptions import (
    StudyNotFoundError,
    StudyAlreadyExistError,
)


class StudyService:
    def __init__(
        self,
        path_to_studies: Path,
        study_factory: StudyFactory,
        path_resources: Path,
    ):
        self.path_to_studies: Path = path_to_studies
        self.study_factory: StudyFactory = study_factory
        self.path_resources: Path = path_resources

    def _extract_info_from_url(self, route: str) -> Tuple[str, str, Path]:
        route_parts = route.split("/")
        uuid = route_parts[0]
        url = "/".join(route_parts[1:])
        study_path = self.path_to_studies / uuid

        return uuid, url, study_path

    def check_study_exist(self, uuid: str) -> None:
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

    def get(self, route: str, parameters: StorageServiceParameters) -> JSON:
        uuid, url, study_path = self._extract_info_from_url(route)
        self.check_study_exist(uuid)

        _, study = self.study_factory.create_from_fs(study_path)
        parts = [item for item in url.split("/") if item]

        data = study.get(parts, depth=parameters.depth)
        del study
        return data

    def get_study_information(self, uuid: str) -> JSON:
        config = StudyConfig(study_path=self.path_to_studies / uuid)
        study = self.study_factory.create_from_config(config)
        return study.get(url=["study"])

    def get_studies_information(self) -> JSON:
        return {
            uuid: self.get_study_information(uuid)
            for uuid in self.get_study_uuids()
        }

    def get_study_path(self, uuid: str) -> Path:
        return self.path_to_studies / uuid

    def create_study(self, study_name: str) -> str:
        empty_study_zip = self.path_resources / "empty-study.zip"

        uuid = StorageServiceUtils.generate_uuid()

        path_study = self.get_study_path(uuid)
        path_study.mkdir()

        with ZipFile(empty_study_zip) as zip_output:
            zip_output.extractall(path=path_study)

        study_data = self.get(
            uuid, parameters=StorageServiceParameters(depth=10)
        )
        StorageServiceUtils.update_antares_info(study_name, study_data)

        _, study = self.study_factory.create_from_fs(path_study)
        study.save(study_data)

        return uuid

    def copy_study(self, src_uuid: str, dest_study_name: str) -> str:
        uuid, url, study_path = self._extract_info_from_url(src_uuid)
        self.check_study_exist(uuid)

        config, study = self.study_factory.create_from_fs(study_path)
        data_source = study.get()
        del study

        uuid = StorageServiceUtils.generate_uuid()
        config.path = self.get_study_path(uuid)
        data_destination = copy.deepcopy(data_source)

        StorageServiceUtils.update_antares_info(
            dest_study_name, data_destination
        )
        if "output" in data_destination:
            del data_destination["output"]
        config.outputs = {}

        study = self.study_factory.create_from_config(config)
        study.save(data_destination)
        del study
        return uuid

    def delete_study(self, name: str) -> None:
        self.check_study_exist(name)
        study_path = self.get_study_path(name)
        shutil.rmtree(study_path)

    def delete_output(self, uuid: str, output_name: str) -> None:
        output_path = self.path_to_studies / uuid / "output" / output_name
        shutil.rmtree(output_path, ignore_errors=True)

    def edit_study(self, route: str, new: JSON) -> JSON:
        # Get data
        uuid, url, study_path = self._extract_info_from_url(route)
        self.check_study_exist(uuid)

        _, study = self.study_factory.create_from_fs(study_path)
        study.save(new, url.split("/"))
        del study
        return new

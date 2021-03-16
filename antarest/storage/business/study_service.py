import copy
import shutil
from pathlib import Path
from typing import List, Tuple, Optional
from zipfile import ZipFile

from antarest.common.config import Config
from antarest.common.custom_types import JSON
from antarest.storage.business.storage_service_utils import StorageServiceUtils
from antarest.storage.model import Metadata
from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.factory import StudyFactory
from antarest.common.requests import (
    RequestParameters,
)
from antarest.storage.web.exceptions import (
    StudyNotFoundError,
    StudyAlreadyExistError,
)


class StudyService:
    def __init__(
        self,
        config: Config,
        study_factory: StudyFactory,
        path_resources: Path,
    ):
        self.config: Config = config
        self.study_factory: StudyFactory = study_factory
        self.path_resources: Path = path_resources

    def check_study_exists(self, metadata: Metadata) -> None:
        if not self.study_exists(metadata):
            raise StudyNotFoundError(
                f"Study with the uuid {metadata.id} does not exist."
            )

    def check_errors(self, metadata: Metadata) -> List[str]:
        path = self.get_study_path(metadata)
        _, study = self.study_factory.create_from_fs(path)
        return study.check_errors(study.get())

    def study_exists(self, metadata: Metadata) -> bool:
        return (self.get_study_path(metadata) / "study.antares").is_file()

    def get_study_uuids(self, workspace: Optional[str] = None) -> List[str]:
        folders: List[Path] = []
        if workspace:
            folders = list(self.get_workspace_path(workspace).iterdir())
        else:
            for w in self.config["storage.workspaces"]:
                folders += list(self.get_workspace_path(w).iterdir())

        studies_list = [
            path.name for path in folders if (path / "study.antares").is_file()
        ]
        # sorting needed for test
        return sorted(studies_list)

    def get(self, metadata: Metadata, url: str = "", depth: int = 3) -> JSON:
        self.check_study_exists(metadata)
        study_path = self.get_study_path(metadata)

        _, study = self.study_factory.create_from_fs(study_path)
        parts = [item for item in url.split("/") if item]

        data = study.get(parts, depth=depth)
        del study
        return data

    def get_study_information(self, metadata: Metadata) -> JSON:
        config = StudyConfig(study_path=self.get_study_path(metadata))
        study = self.study_factory.create_from_config(config)
        return study.get(url=["study"])

    def get_workspace_path(self, workspace: str) -> Path:
        return Path(self.config[f"storage.workspaces.{workspace}.path"])

    def get_study_path(self, metadata: Metadata) -> Path:
        path: Path = self.get_workspace_path(metadata.workspace) / metadata.id
        return path

    def create_study(self, metadata: Metadata) -> Metadata:
        empty_study_zip = self.path_resources / "empty-study.zip"

        path_study = self.get_study_path(metadata)
        path_study.mkdir()

        with ZipFile(empty_study_zip) as zip_output:
            zip_output.extractall(path=path_study)

        study_data = self.get(metadata, url="", depth=10)
        StorageServiceUtils.update_antares_info(metadata, study_data)

        _, study = self.study_factory.create_from_fs(path_study)
        study.save(study_data)

        return metadata

    def copy_study(self, src_meta: Metadata, dest_meta: Metadata) -> Metadata:
        self.check_study_exists(src_meta)
        src_path = self.get_study_path(src_meta)

        config, study = self.study_factory.create_from_fs(src_path)
        data_source = study.get()
        del study

        config.path = self.get_study_path(dest_meta)
        data_destination = copy.deepcopy(data_source)

        StorageServiceUtils.update_antares_info(dest_meta, data_destination)
        if "output" in data_destination:
            del data_destination["output"]
        config.outputs = {}

        study = self.study_factory.create_from_config(config)
        study.save(data_destination)
        del study
        return dest_meta

    def delete_study(self, metadata: Metadata) -> None:
        self.check_study_exists(metadata)
        study_path = self.get_study_path(metadata)
        shutil.rmtree(study_path)

    def delete_output(self, metadata: Metadata, output_name: str) -> None:
        output_path = self.get_study_path(metadata) / "output" / output_name
        shutil.rmtree(output_path, ignore_errors=True)

    def edit_study(self, metadata: Metadata, url: str, new: JSON) -> JSON:
        # Get data
        self.check_study_exists(metadata)

        study_path = self.get_study_path(metadata)
        _, study = self.study_factory.create_from_fs(study_path)
        study.save(new, url.split("/"))
        del study
        return new

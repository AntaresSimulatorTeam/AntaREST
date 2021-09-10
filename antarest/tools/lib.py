import json
import os

import requests
from pathlib import Path
from typing import List, Optional

from requests import Session

from antarest.study.storage.variantstudy.model.model import (
    CommandDTO,
    GenerationResultInfoDTO,
)
from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.config import CacheConfig
from antarest.matrixstore.model import MatrixDTO, MatrixContent
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.common.uri_resolver_service import UriResolverService
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    FileStudy,
    StudyFactory,
)
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
)


class SimpleMatrixService(ISimpleMatrixService):
    def __init__(self, matrix_path: Path):
        self.matrix_path = matrix_path
        assert matrix_path.exists() and matrix_path.is_dir()

    def create(self, data: MatrixContent) -> str:
        pass

    def get(self, id: str) -> Optional[MatrixDTO]:
        pass

    def delete(self, id: str) -> None:
        pass


class CLIVariantManager:
    def __init__(
        self,
        host: Optional[str] = None,
        token: Optional[str] = None,
        session: Optional[Session] = None,
    ):
        self.session = session or requests.session()
        self.host = host
        if session is None and host is None:
            raise ValueError("Missing either session or host")
        if token is not None:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _extract_commands_from_study(
        self, study: FileStudy
    ) -> List[CommandDTO]:
        study_tree = study.tree
        study_config = study.config
        study_commands: List[CommandDTO] = []
        links_commands: List[CommandDTO] = []
        for area_id in study_config.areas:
            area = study_config.areas[area_id]
            area_command = CommandDTO(
                action=CommandName.CREATE_AREA, args={"area_name": area.name}
            )
            study_commands.append(area_command)
            links_data = study_tree.get(
                ["input", "links", area_id, "properties.ini"]
            )
            for link in area.links:
                link_command = CommandDTO(
                    action=CommandName.CREATE_LINK,
                    args={
                        "area1": area_id,
                        "area2": link,
                        "parameters": {},
                        "series": [],
                    },
                )
                link_data = links_data.get(link)
                link_config_command = CommandDTO(
                    action=CommandName.UPDATE_CONFIG,
                    args={
                        "target": f"input/links/{area_id}/properties/{link}",
                        "data": link_data,
                    },
                )
                links_commands.append(link_command)
                links_commands.append(link_config_command)
            for thermal in area.thermals:
                CommandDTO(action=CommandName.CREATE_CLUSTER, args={})

        study_commands += links_commands
        return study_commands

    def extract_commands(self, study_path: Path, commands_output_dir: Path):
        if not commands_output_dir.exists():
            commands_output_dir.mkdir(parents=True)
        matrices_dir = commands_output_dir / "matrices"
        matrices_dir.mkdir()

        matrix_service = SimpleMatrixService(matrices_dir)
        matrix_resolver = UriResolverService(matrix_service)
        study_factory = StudyFactory(
            matrix=matrix_service,
            resolver=matrix_resolver,
            cache=LocalCache(CacheConfig()),
        )

        study_config, study_tree = study_factory.create_from_fs(
            study_path, str(study_path), False
        )
        command_list = self._extract_commands_from_study(
            FileStudy(study_config, study_tree)
        )

        with open(commands_output_dir / "commands.json", "w") as fh:
            json.dump([command.dict() for command in command_list], fh)

    def parse_commands(self, file: Path) -> List[CommandDTO]:
        with open(file, "r") as fh:
            json_commands = json.load(fh)

        commands: List[CommandDTO] = []
        for command in json_commands:
            commands.append(CommandDTO.parse_obj(command))

        return commands

    def apply_commands(
        self,
        study_id: str,
        commands: List[CommandDTO],
        matrices_dir: Optional[Path],
    ) -> GenerationResultInfoDTO:
        study = self.session.get(
            self.build_url(f"/v1/studies/{study_id}")
        ).json()
        assert study is not None

        if matrices_dir:
            matrix_dataset: List[str] = []
            for matrix in os.listdir(matrices_dir):
                with open(matrices_dir / matrix, "r") as fh:
                    matrix_data = json.load(fh)
                    res = self.session.post(
                        self.build_url(f"/v1/matrix"), json=matrix_data
                    )
                    assert res.status_code == 200
                    matrix_id = res.json()
                    assert matrix_id == matrix
                    matrix_dataset.append(matrix_id)
            # TODO could create a dataset from theses matrices using "variant_<study_id>" as name
            # also the matrix could be named after the command name where they are used

        res = self.session.post(
            self.build_url(f"/v1/studies/{study_id}/commands"),
            json=[command.dict() for command in commands],
        )
        assert res.status_code == 200

        res = self.session.put(
            self.build_url(f"/v1/studies/{study_id}/generate?denormalize=true")
        )
        assert res.status_code == 200
        return GenerationResultInfoDTO.parse_obj(res.json())

    def build_url(self, url: str) -> str:
        if self.host is not None:
            return f"{self.host}/{url}"
        return url

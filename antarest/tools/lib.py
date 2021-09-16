import json
import logging
import os
import time

import requests
from pathlib import Path
from typing import List, Optional, Union, Callable

from requests import Session

from antarest.core.custom_types import JSON
from antarest.core.utils.utils import StopWatch
from antarest.matrixstore.repository import MatrixContentRepository
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import INode
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)
from antarest.study.storage.rawstudy.model.filesystem.utils import (
    traverse_tree,
)
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    CreateBindingConstraint,
)
from antarest.study.storage.variantstudy.model.command.create_cluster import (
    CreateCluster,
)
from antarest.study.storage.variantstudy.model.command.create_link import (
    CreateLink,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.replace_matrix import (
    ReplaceMatrix,
)
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)
from antarest.study.storage.variantstudy.model.command.utils import (
    strip_matrix_protocol,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)
from antarest.study.storage.variantstudy.model.model import (
    CommandDTO,
    GenerationResultInfoDTO,
)
from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.config import CacheConfig, Config, StorageConfig
from antarest.matrixstore.model import MatrixDTO, MatrixContent, MatrixData
from antarest.matrixstore.service import (
    ISimpleMatrixService,
    MatrixService,
    SimpleMatrixService,
)
from antarest.study.common.uri_resolver_service import UriResolverService
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    FileStudy,
    StudyFactory,
)
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    TimeStep,
    BindingConstraintOperator,
)
from antarest.study.storage.variantstudy.variant_command_extractor import (
    VariantCommandsExtractor,
)

logger = logging.getLogger(__name__)


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

    @staticmethod
    def extract_commands(study_path: Path, commands_output_dir: Path) -> None:
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
        local_matrix_service = SimpleMatrixService(matrices_dir)
        extractor = VariantCommandsExtractor(local_matrix_service)
        command_list = extractor.extract(FileStudy(study_config, study_tree))

        with open(commands_output_dir / "commands.json", "w") as fh:
            json.dump(
                [command.dict(exclude={"id"}) for command in command_list], fh
            )

    @staticmethod
    def parse_commands(file: Path) -> List[CommandDTO]:
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
        stopwatch = StopWatch()
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
            stopwatch.log_elapsed(
                lambda x: logger.info(f"Matrix upload done in {x}ms")
            )

        res = self.session.post(
            self.build_url(f"/v1/studies/{study_id}/commands"),
            json=[command.dict() for command in commands],
        )
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Command upload done in {x}ms")
        )
        assert res.status_code == 200

        res = self.session.put(
            self.build_url(f"/v1/studies/{study_id}/generate?denormalize=true")
        )
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Generation done in {x}ms")
        )
        assert res.status_code == 200
        return GenerationResultInfoDTO.parse_obj(res.json())

    def build_url(self, url: str) -> str:
        if self.host is not None:
            return f"{self.host}/{url}"
        return url

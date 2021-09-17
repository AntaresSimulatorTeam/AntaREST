import json
import logging
import os
import shutil
import time

import requests
from pathlib import Path
from typing import List, Optional, Union, Callable, Set

from requests import Session

from antarest.core.utils.utils import StopWatch
from antarest.study.storage.variantstudy.model.command.utils import (
    strip_matrix_protocol,
)
from antarest.study.storage.variantstudy.model.model import (
    CommandDTO,
    GenerationResultInfoDTO,
)
from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.config import CacheConfig, Config, StorageConfig
from antarest.matrixstore.service import (
    SimpleMatrixService,
)
from antarest.study.common.uri_resolver_service import UriResolverService
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    FileStudy,
    StudyFactory,
)
from antarest.study.storage.variantstudy.variant_command_extractor import (
    VariantCommandsExtractor,
)

logger = logging.getLogger(__name__)
COMMAND_FILE = "commands.json"
MATRIX_STORE_DIR = "matrices"


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
        matrices_dir = commands_output_dir / MATRIX_STORE_DIR
        matrices_dir.mkdir()

        matrix_service = SimpleMatrixService(matrices_dir)
        matrix_resolver = UriResolverService(matrix_service)
        study_factory = StudyFactory(
            matrix=matrix_service,
            resolver=matrix_resolver,
            cache=LocalCache(CacheConfig()),
        )

        study_config, study_tree = study_factory.create_from_fs(
            study_path, str(study_path), use_cache=False
        )
        local_matrix_service = SimpleMatrixService(matrices_dir)
        extractor = VariantCommandsExtractor(local_matrix_service)
        command_list = extractor.extract(FileStudy(study_config, study_tree))

        with open(commands_output_dir / COMMAND_FILE, "w") as fh:
            json.dump(
                [command.dict(exclude={"id"}) for command in command_list], fh
            )

    @staticmethod
    def generate_diff(base: Path, variant: Path, output_dir: Path) -> None:
        if not output_dir.exists():
            output_dir.mkdir(parents=True)
        matrices_dir = output_dir / MATRIX_STORE_DIR
        matrices_dir.mkdir(exist_ok=True)

        base_command_file = base / COMMAND_FILE
        if not base_command_file.exists():
            raise ValueError(f"Missing {COMMAND_FILE}")
        variant_command_file = variant / COMMAND_FILE
        if not variant_command_file.exists():
            raise ValueError(f"Missing {COMMAND_FILE}")

        if (base / MATRIX_STORE_DIR).exists():
            for matrix_file in os.listdir(base / MATRIX_STORE_DIR):
                shutil.copyfile(
                    base / MATRIX_STORE_DIR / matrix_file,
                    matrices_dir / matrix_file,
                )
        if (variant / MATRIX_STORE_DIR).exists():
            for matrix_file in os.listdir(variant / MATRIX_STORE_DIR):
                shutil.copyfile(
                    variant / MATRIX_STORE_DIR / matrix_file,
                    matrices_dir / matrix_file,
                )

        local_matrix_service = SimpleMatrixService(matrices_dir)
        extractor = VariantCommandsExtractor(local_matrix_service)
        diff_commands = extractor.diff(
            CLIVariantManager.parse_commands(base_command_file),
            CLIVariantManager.parse_commands(variant_command_file),
        )

        with open(output_dir / COMMAND_FILE, "w") as fh:
            json.dump(
                [
                    command.to_dto().dict(exclude={"id"})
                    for command in diff_commands
                ],
                fh,
            )
        needed_matrices: Set[str] = set()
        for command in diff_commands:
            for matrix in command.get_inner_matrices():
                needed_matrices.add(strip_matrix_protocol(matrix))
        for matrix_file in os.listdir(matrices_dir):
            if matrix_file not in needed_matrices:
                os.unlink(matrices_dir / matrix_file)

    @staticmethod
    def parse_commands(file: Path) -> List[CommandDTO]:
        with open(file, "r") as fh:
            json_commands = json.load(fh)

        commands: List[CommandDTO] = []
        for command in json_commands:
            commands.append(CommandDTO.parse_obj(command))

        return commands

    def apply_commands_from_dir(
        self, study_id: str, command_dir: Path
    ) -> GenerationResultInfoDTO:
        matrix_dir: Optional[Path] = command_dir / MATRIX_STORE_DIR
        command_file = command_dir / COMMAND_FILE
        if matrix_dir and not matrix_dir.exists():
            matrix_dir = None
        if not command_file.exists():
            raise ValueError(f"Missing {COMMAND_FILE}")

        commands = CLIVariantManager.parse_commands(command_file)
        return self.apply_commands(study_id, commands, matrix_dir)

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

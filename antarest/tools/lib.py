# Copyright (c) 2024, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import json
import logging
import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Set, Union
from zipfile import ZipFile

import numpy as np
from httpx import Client

from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.config import CacheConfig
from antarest.core.tasks.model import TaskDTO
from antarest.core.utils.utils import StopWatch, get_local_path
from antarest.matrixstore.repository import MatrixContentRepository
from antarest.matrixstore.service import SimpleMatrixService
from antarest.matrixstore.uri_resolver_service import UriResolverService
from antarest.study.model import NEW_DEFAULT_STUDY_VERSION, STUDY_REFERENCE_TEMPLATES
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.utils import create_new_empty_study
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO, GenerationResultInfoDTO
from antarest.study.storage.variantstudy.variant_command_extractor import VariantCommandsExtractor
from antarest.study.storage.variantstudy.variant_command_generator import VariantCommandGenerator
from antarest.utils import from_json, to_json

logger = logging.getLogger(__name__)
COMMAND_FILE = "commands.json"
MATRIX_STORE_DIR = "matrices"


class IVariantGenerator(ABC):
    @abstractmethod
    def apply_commands(self, commands: List[CommandDTO], matrices_dir: Path) -> GenerationResultInfoDTO:
        raise NotImplementedError()


def set_auth_token(client: Client, auth_token: Optional[str] = None) -> Client:
    if auth_token is not None:
        client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return client


def create_http_client(verify: bool, auth_token: Optional[str] = None) -> Client:
    client = Client(verify=verify)
    set_auth_token(client, auth_token)
    return client


class RemoteVariantGenerator(IVariantGenerator):
    def __init__(
        self,
        study_id: str,
        host: str,
        session: Client,
    ):
        self.study_id = study_id
        self.session = session
        self.host = host

    def apply_commands(
        self,
        commands: List[CommandDTO],
        matrices_dir: Path,
    ) -> GenerationResultInfoDTO:
        stopwatch = StopWatch()

        logger.info("Uploading matrices")
        matrix_dataset: List[str] = []
        for matrix_file in matrices_dir.iterdir():
            matrix = np.loadtxt(matrix_file, delimiter="\t", dtype=np.float64, ndmin=2)
            matrix = matrix.reshape((1, 0)) if matrix.size == 0 else matrix
            matrix_data = matrix.tolist()
            res = self.session.post(self.build_url("/v1/matrix"), json=matrix_data)
            res.raise_for_status()
            matrix_id = res.json()
            matrix_dataset.append(matrix_id)

        # TODO could create a dataset from theses matrices using "variant_<study_id>" as name
        # also the matrix could be named after the command name where they are used
        stopwatch.log_elapsed(lambda x: logger.info(f"Matrix upload done in {x}s"))

        res = self.session.post(
            self.build_url(f"/v1/studies/{self.study_id}/commands"),
            json=[command.model_dump() for command in commands],
        )
        res.raise_for_status()
        stopwatch.log_elapsed(lambda x: logger.info(f"Command upload done in {x}s"))

        res = self.session.put(self.build_url(f"/v1/studies/{self.study_id}/generate?denormalize=true"))
        res.raise_for_status()

        task_id = res.json()
        res = self.session.get(self.build_url(f"/v1/tasks/{task_id}?wait_for_completion=true"))
        res.raise_for_status()

        stopwatch.log_elapsed(lambda x: logger.info(f"Generation done in {x}s"))
        task_result = TaskDTO(**res.json())

        if task_result.result is None or task_result.result.return_value is None:  # pragma: no cover
            # This should not happen, but if it does, we return a failed result
            return GenerationResultInfoDTO(success=False, details=[])

        info = from_json(task_result.result.return_value)
        return GenerationResultInfoDTO(**info)

    def build_url(self, url: str) -> str:
        return url if self.host is None else f"{self.host.strip('/')}/{url.strip('/')}"


class LocalVariantGenerator(IVariantGenerator):
    def __init__(self, output_path: Path):
        self.output_path = output_path

    def render_template(self, study_version: str = NEW_DEFAULT_STUDY_VERSION) -> None:
        version_template = STUDY_REFERENCE_TEMPLATES[study_version]
        empty_study_zip = get_local_path() / "resources" / version_template
        with ZipFile(empty_study_zip) as zip_output:
            zip_output.extractall(path=self.output_path)
            # remove preexisting sets
            sets_ini = self.output_path.joinpath("input/areas/sets.ini")
            sets_ini.write_bytes(b"")

    def apply_commands(self, commands: List[CommandDTO], matrices_dir: Path) -> GenerationResultInfoDTO:
        stopwatch = StopWatch()
        matrix_content_repository = MatrixContentRepository(
            bucket_dir=matrices_dir,
        )
        matrix_service = SimpleMatrixService(
            matrix_content_repository=matrix_content_repository,
        )
        matrix_resolver = UriResolverService(matrix_service)
        local_cache = LocalCache(CacheConfig())
        study_factory = StudyFactory(
            matrix=matrix_service,
            resolver=matrix_resolver,
            cache=local_cache,
        )
        generator = VariantCommandGenerator(study_factory)
        generator_matrix_constants = GeneratorMatrixConstants(matrix_service)
        generator_matrix_constants.init_constant_matrices()
        command_factory = CommandFactory(
            generator_matrix_constants=generator_matrix_constants,
            matrix_service=matrix_service,
            patch_service=PatchService(),
        )

        command_objs: List[List[ICommand]] = []
        logger.info("Parsing command objects...")
        command_objs.extend(command_factory.to_command(command_block) for command_block in commands)
        stopwatch.log_elapsed(lambda x: logger.info(f"Command objects parsed in {x}s"))
        result = generator.generate(command_objs, self.output_path, delete_on_failure=False)
        if result.success:
            # sourcery skip: extract-method
            logger.info("Building new study tree...")
            study = study_factory.create_from_fs(self.output_path, study_id="", use_cache=False)
            logger.info("Denormalize study...")
            stopwatch.reset_current()
            study.tree.denormalize()
            stopwatch.log_elapsed(lambda x: logger.info(f"Denormalized done in {x}s"))
        return result


def extract_commands(study_path: Path, commands_output_dir: Path) -> None:
    if not commands_output_dir.exists():
        commands_output_dir.mkdir(parents=True)
    matrices_dir = commands_output_dir / MATRIX_STORE_DIR
    matrices_dir.mkdir()
    matrix_content_repository = MatrixContentRepository(
        bucket_dir=matrices_dir,
    )
    matrix_service = SimpleMatrixService(
        matrix_content_repository=matrix_content_repository,
    )
    matrix_resolver = UriResolverService(matrix_service)
    cache = LocalCache(CacheConfig())
    study_factory = StudyFactory(
        matrix=matrix_service,
        resolver=matrix_resolver,
        cache=cache,
    )

    study = study_factory.create_from_fs(study_path, str(study_path), use_cache=False)
    matrix_content_repository = MatrixContentRepository(
        bucket_dir=matrices_dir,
    )
    local_matrix_service = SimpleMatrixService(
        matrix_content_repository=matrix_content_repository,
    )
    extractor = VariantCommandsExtractor(local_matrix_service, patch_service=PatchService())
    command_list = extractor.extract(study)

    (commands_output_dir / COMMAND_FILE).write_text(
        to_json([command.model_dump(exclude={"id"}) for command in command_list], indent=2).decode("utf-8")
    )


def generate_diff(
    base: Path,
    variant: Path,
    output_dir: Path,
    study_version: str = NEW_DEFAULT_STUDY_VERSION,
) -> None:
    """
    Generate variant script commands from two variant script directories.

    This function generates a set of commands that can be used to transform
    the base study into the variant study, based on the differences between the two.
    It does this by comparing the command files in each study directory
    and extracting the differences between them.

    Args:
        base: The directory of the base study.
        variant: The directory of the variant study.
        output_dir: The output directory where the generated commands will be saved.
        study_version: The version of the generated study.

    Raises:
        FileNotFoundError: If the base or variant study's command file is missing.

    Returns:
        None. The generated commands are written to a JSON file in the specified output directory.
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    matrices_dir = output_dir / MATRIX_STORE_DIR
    matrices_dir.mkdir(exist_ok=True)

    study_id = "empty_base"
    path_study = output_dir / study_id

    matrix_content_repository = MatrixContentRepository(
        bucket_dir=matrices_dir,
    )
    local_matrix_service = SimpleMatrixService(
        matrix_content_repository=matrix_content_repository,
    )
    resolver = UriResolverService(matrix_service=local_matrix_service)

    cache = LocalCache()
    study_factory = StudyFactory(matrix=local_matrix_service, resolver=resolver, cache=cache)

    create_new_empty_study(
        version=study_version,
        path_study=path_study,
        path_resources=get_local_path() / "resources",
    )

    empty_study = study_factory.create_from_fs(path_study, study_id)

    base_command_file = base / COMMAND_FILE
    if not base_command_file.exists():
        raise FileNotFoundError(f"Missing {COMMAND_FILE}")
    variant_command_file = variant / COMMAND_FILE
    if not variant_command_file.exists():
        raise FileNotFoundError(f"Missing {COMMAND_FILE}")

    stopwatch = StopWatch()
    logger.info("Copying input matrices")
    if (base / MATRIX_STORE_DIR).exists():
        for matrix_file in os.listdir(base / MATRIX_STORE_DIR):
            shutil.copyfile(
                base / MATRIX_STORE_DIR / matrix_file,
                matrices_dir / matrix_file,
            )
    stopwatch.log_elapsed(lambda x: logger.info(f"Base input matrix copied in {x}s"))
    if (variant / MATRIX_STORE_DIR).exists():
        for matrix_file in os.listdir(variant / MATRIX_STORE_DIR):
            shutil.copyfile(
                variant / MATRIX_STORE_DIR / matrix_file,
                matrices_dir / matrix_file,
            )
    stopwatch.log_elapsed(lambda x: logger.info(f"Variant input matrix copied in {x}s"))

    extractor = VariantCommandsExtractor(local_matrix_service, patch_service=PatchService())
    diff_commands = extractor.diff(
        base=parse_commands(base_command_file),
        variant=parse_commands(variant_command_file),
        empty_study=empty_study,
    )

    (output_dir / COMMAND_FILE).write_text(
        to_json(
            [command.to_dto().model_dump(exclude={"id"}) for command in diff_commands],
            indent=2,
        ).decode("utf-8")
    )

    needed_matrices: Set[str] = set()
    for command in diff_commands:
        for matrix in command.get_inner_matrices():
            needed_matrices.add(f"{matrix}.tsv")
    for matrix_file in os.listdir(matrices_dir):
        if matrix_file not in needed_matrices:
            os.unlink(matrices_dir / matrix_file)


def parse_commands(file: Path) -> List[CommandDTO]:
    stopwatch = StopWatch()
    logger.info("Parsing commands script")
    with open(file, "r") as fh:
        json_commands = json.load(fh)
    stopwatch.log_elapsed(lambda x: logger.info(f"Script file read in {x}s"))

    commands: List[CommandDTO] = [CommandDTO(**command) for command in json_commands]
    stopwatch.log_elapsed(lambda x: logger.info(f"Script commands parsed in {x}s"))

    return commands


def generate_study(
    commands_dir: Path,
    study_id: Optional[str],
    output: Optional[str] = None,
    host: Optional[str] = None,
    session: Optional[Client] = None,
    study_version: str = NEW_DEFAULT_STUDY_VERSION,
) -> GenerationResultInfoDTO:
    """
    Generate a new study or update an existing study by applying commands.

    Args:
        commands_dir: The directory containing the command file and input matrices.
        study_id: The ID of the base study to use for generating the new study.
            If `host` is provided, this is ignored.
        output: The output directory where the new study will be generated.
            If `study_id` and `host` are not provided, this must be specified.
        host: The URL of the Antares server to use for generating the new study.
            If `study_id` is not provided, this is ignored.
        session: The session to use when connecting to the Antares server.
            If `host` is not provided, this is ignored.
        study_version: The target version of the generated study.

    Returns:
        GenerationResultInfoDTO: A data transfer object containing information about the generation result.
    """
    generator: Union[RemoteVariantGenerator, LocalVariantGenerator]

    if study_id is not None and host is not None and session is not None:
        generator = RemoteVariantGenerator(study_id, host, session)
    elif output is None:
        raise TypeError("'output' must be set")
    else:
        output_dir = Path(output)
        generator = LocalVariantGenerator(output_dir)
        if not output_dir.exists():
            output_dir.mkdir(parents=True)
            generator.render_template(study_version)
    # Apply commands from the commands dir
    matrix_dir: Path = commands_dir / MATRIX_STORE_DIR
    command_file = commands_dir / COMMAND_FILE
    if matrix_dir and not matrix_dir.exists():
        matrix_dir.mkdir()
    if not command_file.exists():
        raise FileNotFoundError(f"Missing {COMMAND_FILE}")
    commands = parse_commands(command_file)
    return generator.apply_commands(commands, matrix_dir)

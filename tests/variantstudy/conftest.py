import hashlib
import zipfile
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest
from antarest.matrixstore.service import MatrixService
from antarest.matrixstore.uri_resolver_service import UriResolverService
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)
from tests.variantstudy.assets import ASSETS_DIR


@pytest.fixture(name="matrix_service")
def matrix_service_fixture() -> MatrixService:
    """
    Fixture for creating a mocked matrix service.

    Returns:
        An instance of the `SimpleMatrixService` class representing the matrix service.
    """

    def create(data):
        """
        This function calculates a unique ID for each matrix, without storing
        any data in the file system or the database.
        """
        matrix = (
            data
            if isinstance(data, np.ndarray)
            else np.array(data, dtype=np.float64)
        )
        matrix_hash = hashlib.sha256(matrix.data).hexdigest()
        return matrix_hash

    matrix_service = Mock(spec=MatrixService)
    matrix_service.create.side_effect = create
    return matrix_service


@pytest.fixture(name="command_context")
def command_context_fixture(matrix_service: MatrixService) -> CommandContext:
    """
    Fixture for creating a CommandContext object.

    Args:
        matrix_service: The MatrixService object.

    Returns:
        CommandContext: The CommandContext object.
    """
    # sourcery skip: inline-immediately-returned-variable
    command_context = CommandContext(
        generator_matrix_constants=GeneratorMatrixConstants(
            matrix_service=matrix_service
        ),
        matrix_service=matrix_service,
        patch_service=PatchService(
            repository=Mock(spec=StudyMetadataRepository)
        ),
    )
    return command_context


@pytest.fixture(name="command_factory")
def command_factory_fixture(matrix_service: MatrixService) -> CommandFactory:
    """
    Fixture for creating a CommandFactory object.

    Args:
        matrix_service: The MatrixService object.

    Returns:
        CommandFactory: The CommandFactory object.
    """
    return CommandFactory(
        generator_matrix_constants=GeneratorMatrixConstants(
            matrix_service=matrix_service
        ),
        matrix_service=matrix_service,
        patch_service=PatchService(),
    )


@pytest.fixture(name="empty_study")
def empty_study_fixture(
    tmp_path: Path, matrix_service: MatrixService
) -> FileStudy:
    """
    Fixture for creating an empty FileStudy object.

    Args:
        tmp_path: The temporary path for extracting the empty study.
        matrix_service: The MatrixService object.

    Returns:
        FileStudy: The empty FileStudy object.
    """
    empty_study_path: Path = ASSETS_DIR / "empty_study_720.zip"
    empty_study_destination_path = tmp_path.joinpath("empty-study")
    with zipfile.ZipFile(empty_study_path, "r") as zip_empty_study:
        zip_empty_study.extractall(empty_study_destination_path)

    config = FileStudyTreeConfig(
        study_path=empty_study_destination_path,
        path=empty_study_destination_path,
        study_id="",
        version=720,
        areas={},
        sets={},
    )
    # sourcery skip: inline-immediately-returned-variable
    file_study = FileStudy(
        config=config,
        tree=FileStudyTree(
            context=ContextServer(
                matrix=matrix_service,
                resolver=UriResolverService(matrix_service=matrix_service),
            ),
            config=config,
        ),
    )
    return file_study

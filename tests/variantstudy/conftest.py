import zipfile
from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine

from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.dbmodel import Base
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


@pytest.fixture
def matrix_service() -> MatrixService:
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    # noinspection PyTypeChecker,SpellCheckingInspection
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    matrix_service = Mock(spec=MatrixService)
    matrix_service.create.side_effect = (
        lambda data: data if isinstance(data, str) else "matrix_id"
    )

    return matrix_service


@pytest.fixture
def command_context(matrix_service: MatrixService) -> CommandContext:
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


@pytest.fixture
def command_factory(matrix_service: MatrixService) -> CommandFactory:
    return CommandFactory(
        generator_matrix_constants=GeneratorMatrixConstants(
            matrix_service=matrix_service
        ),
        matrix_service=matrix_service,
        patch_service=PatchService(),
    )


@pytest.fixture
def empty_study(tmp_path: Path, matrix_service: MatrixService) -> FileStudy:
    project_dir: Path = Path(__file__).parent.parent.parent
    empty_study_path: Path = project_dir / "resources" / "empty_study_720.zip"
    empty_study_destination_path = tmp_path.joinpath("empty-study")
    with zipfile.ZipFile(empty_study_path, "r") as zip_empty_study:
        zip_empty_study.extractall(empty_study_destination_path)

    config = FileStudyTreeConfig(
        study_path=empty_study_destination_path,
        path=empty_study_destination_path,
        study_id="",
        version=700,
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

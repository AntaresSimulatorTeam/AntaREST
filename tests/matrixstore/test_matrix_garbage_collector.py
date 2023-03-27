from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine

from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware, db
from antarest.dbmodel import Base
from antarest.matrixstore.matrix_garbage_collector import (
    MatrixGarbageCollector,
)
from antarest.matrixstore.model import MatrixDataSet, MatrixDataSetRelation
from antarest.matrixstore.repository import MatrixDataSetRepository
from antarest.matrixstore.service import MatrixService
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
)
from antarest.study.storage.variantstudy.model.dbmodel import CommandBlock
from antarest.study.storage.variantstudy.repository import (
    VariantStudyRepository,
)


@pytest.fixture
def matrix_garbage_collector(tmp_path: Path):
    """
    Fixture for creating a MatrixGarbageCollector object.
    """
    matrix_store = tmp_path / "matrix_store"
    matrix_store.mkdir()
    default_workspace = tmp_path / "default_workspace"
    default_workspace.mkdir()
    mock_workspace_config = Mock()
    mock_workspace_config.path = default_workspace

    mock_config = Mock()
    mock_config.storage.matrixstore = matrix_store
    mock_config.storage.workspaces = {"default": mock_workspace_config}
    mock_config.storage.matrix_gc_dry_run = False

    matrix_constant_generator = Mock(spec=GeneratorMatrixConstants)
    matrix_constant_generator.hashes = {"test": "constant_matrix"}
    command_factory = CommandFactory(
        generator_matrix_constants=matrix_constant_generator,
        matrix_service=Mock(spec=MatrixService),
        patch_service=Mock(spec=PatchService),
    )
    study_service = Mock()
    study_service.storage_service.variant_study_service.command_factory = (
        command_factory
    )
    study_service.storage_service.variant_study_service.repository = (
        VariantStudyRepository(cache_service=Mock())
    )

    matrix_garbage_collector = MatrixGarbageCollector(
        config=mock_config, study_service=study_service, matrix_service=Mock()
    )

    return matrix_garbage_collector


@pytest.mark.unit_test
def test_get_saved_matrices(
    matrix_garbage_collector: MatrixGarbageCollector,
):
    """
    Test that the get_all_saved_matrices function returns a list of all saved
    matrices.
    """
    matrix_name1 = "matrix_name1"
    matrix_name2 = "matrix_name2"
    (
        matrix_garbage_collector.saved_matrices_path / f"{matrix_name1}.txt"
    ).touch()
    (
        matrix_garbage_collector.saved_matrices_path / f"{matrix_name2}.txt"
    ).touch()

    # Get all saved matrices
    saved_matrices = matrix_garbage_collector._get_saved_matrices()
    assert saved_matrices == {matrix_name1, matrix_name2}


@pytest.mark.unit_test
def test_get_matrices_used_in_raw_studies(
    matrix_garbage_collector: MatrixGarbageCollector,
):
    """
    Test that the get_matrices_used_in_raw_studies function returns a list of
    all matrices used in raw studies.
    """
    matrix_name1 = "matrix_name1"
    matrix_name2 = "matrix_name2"
    matrix_name3 = "matrix_name3"
    matrix_name4 = "matrix_name4"

    raw_study_path = (
        matrix_garbage_collector.managed_studies_path / "raw_study"
    )
    raw_study_path.mkdir()
    (raw_study_path / f"{matrix_name1}.link").write_text(
        f"matrix://{matrix_name1}"
    )
    (raw_study_path / f"{matrix_name2}.link").write_text(
        f"matrix://{matrix_name2}"
    )
    (raw_study_path / f"{matrix_name3}.link").write_text(
        f"matrix://{matrix_name3}"
    )
    (raw_study_path / f"{matrix_name4}.txt").write_text(
        f"matrix://{matrix_name4}"
    )

    output = matrix_garbage_collector._get_raw_studies_matrices()

    assert len(output) == 3
    assert matrix_name1 in output
    assert matrix_name2 in output
    assert matrix_name3 in output
    assert matrix_name4 not in output


@pytest.mark.unit_test
def test_get_matrices_used_in_variant_studies(
    matrix_garbage_collector: MatrixGarbageCollector,
):
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )
    with db():
        study_id = "study_id"
        # TODO: add series to the command blocks
        command_block1 = CommandBlock(
            study_id=study_id,
            command=CommandName.CREATE_LINK.value,
            args='{"area1": "area1", "area2": "area2"}',
            index=0,
            version=7,
        )
        command_block2 = CommandBlock(
            study_id=study_id,
            command=CommandName.CREATE_LINK.value,
            args='{"area1": "area2", "area2": "area3"}',
            index=0,
            version=7,
        )
        db.session.add(command_block1)
        db.session.add(command_block2)
        db.session.commit()
        matrices = matrix_garbage_collector._get_variant_studies_matrices()
        assert not matrices
        command_block1 = CommandBlock(
            study_id=study_id,
            command=CommandName.CREATE_LINK.value,
            args='{"area1": "area1", "area2": "area2","series": "[[1,2,3]]"}',
            index=0,
            version=7,
        )
        command_block2 = CommandBlock(
            study_id=study_id,
            command=CommandName.CREATE_LINK.value,
            args='{"area1": "area2", "area2": "area3","series": "[[1,2,4]]"}',
            index=0,
            version=7,
        )
        db.session.add(command_block1)
        db.session.add(command_block2)
        db.session.commit()
        matrices = matrix_garbage_collector._get_variant_studies_matrices()
        assert len(matrices) == 2
        assert "[[1,2,3]]" in matrices
        assert "[[1,2,4]]" in matrices


@pytest.mark.unit_test
def test_get_matrices_used_in_dataset(
    matrix_garbage_collector: MatrixGarbageCollector,
):
    matrix_garbage_collector.dataset_repository = MatrixDataSetRepository()
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    dataset = MatrixDataSet(
        name="name",
        public=True,
        owner_id="owner_id",
        groups=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    matrix_relation1 = MatrixDataSetRelation(name="matrix_name1")
    matrix_relation1.matrix_id = "matrix_id1"
    dataset.matrices.append(matrix_relation1)
    matrix_relation2 = MatrixDataSetRelation(name="matrix_name2")
    matrix_relation2.matrix_id = "matrix_id2"
    dataset.matrices.append(matrix_relation2)
    with db():
        db.session.add(dataset)
        db.session.commit()
        matrices = matrix_garbage_collector._get_datasets_matrices()
        assert len(matrices) == 2
        assert "matrix_id1" in matrices
        assert "matrix_id2" in matrices


@pytest.mark.unit_test
def test_get_used_matrices(matrix_garbage_collector: MatrixGarbageCollector):
    matrix_garbage_collector._get_raw_studies_matrices = Mock(
        return_value={"matrix1", "matrix2"}
    )
    matrix_garbage_collector._get_variant_studies_matrices = Mock(
        return_value={"matrix3", "matrix4"}
    )
    matrix_garbage_collector._get_datasets_matrices = Mock(
        return_value={"matrix4", "matrix6"}
    )
    assert matrix_garbage_collector._get_used_matrices() == {
        "matrix1",
        "matrix2",
        "matrix3",
        "matrix4",
        "matrix6",
        "constant_matrix",
    }


@pytest.mark.unit_test
def test_delete_unused_saved_matrices(
    matrix_garbage_collector: MatrixGarbageCollector,
):
    unused_matrices = {"matrix1", "matrix2"}
    matrix_garbage_collector.matrix_service.delete = Mock()
    matrix_garbage_collector._delete_unused_saved_matrices(unused_matrices)

    matrix_garbage_collector.matrix_service.delete.assert_any_call("matrix1")
    matrix_garbage_collector.matrix_service.delete.assert_any_call("matrix2")

    matrix_garbage_collector.dry_run = True
    matrix_garbage_collector.matrix_service.delete.reset_mock()
    matrix_garbage_collector._delete_unused_saved_matrices(unused_matrices)
    matrix_garbage_collector.matrix_service.delete.assert_not_called()


@pytest.mark.unit_test
def test_clean_matrices(matrix_garbage_collector: MatrixGarbageCollector):
    matrix_garbage_collector._get_saved_matrices = Mock(
        return_value={"matrix1", "matrix2"}
    )
    matrix_garbage_collector._get_used_matrices = Mock(
        return_value={"matrix1"}
    )
    matrix_garbage_collector._delete_unused_saved_matrices = Mock()

    matrix_garbage_collector._clean_matrices()

    matrix_garbage_collector._delete_unused_saved_matrices.assert_called_once_with(
        unused_matrices={"matrix2"}
    )

# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest
from helpers import with_admin_user, with_db_context

from antarest.blobstore.service import BlobService
from antarest.core.config import InternalMatrixFormat
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.matrix_garbage_collector import MatrixGarbageCollector
from antarest.matrixstore.model import MatrixMetadataDTO, MatrixReference
from antarest.matrixstore.repository import MatrixContentRepository, MatrixDataSetRepository, MatrixRepository
from antarest.matrixstore.service import MatrixService
from antarest.study.business.model.thermal_cluster_model import ThermalClusterCreation
from antarest.study.model import RawStudy
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_cluster import CreateCluster
from antarest.study.storage.variantstudy.model.command.generate_thermal_cluster_timeseries import (
    GenerateThermalClusterTimeSeries,
)
from antarest.study.storage.variantstudy.repository import VariantStudyRepository
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService


@pytest.fixture
def matrix_garbage_collector(tmp_path: Path) -> MatrixGarbageCollector:
    """
    Fixture for creating a MatrixGarbageCollector object.
    """
    default_workspace = tmp_path / "default_workspace"
    default_workspace.mkdir()
    mock_workspace_config = Mock()
    mock_workspace_config.path = default_workspace

    matrix_constant_generator = Mock(spec=GeneratorMatrixConstants)
    matrix_constant_generator.hashes = {"test": "constant_matrix"}
    command_factory = CommandFactory(
        generator_matrix_constants=matrix_constant_generator,
        matrix_service=Mock(spec=MatrixService),
        blob_service=Mock(spec=BlobService),
    )
    study_service = Mock()
    study_service.storage_service.variant_study_service.command_factory = command_factory
    study_service.storage_service.variant_study_service.repository = VariantStudyRepository(cache_service=Mock())

    matrix_garbage_collector = MatrixGarbageCollector(
        matrix_service=Mock(), dry_run=False, sleeping_time=3600, retention_time=3600
    )

    return matrix_garbage_collector


def test_delete_unused_saved_matrices(
    matrix_garbage_collector: MatrixGarbageCollector,
) -> None:
    unused_matrices = {"matrix1", "matrix2"}
    matrix_garbage_collector.matrix_service.delete = Mock()
    matrix_garbage_collector._delete_unused_saved_matrices(unused_matrices)

    matrix_garbage_collector.matrix_service.delete.assert_any_call("matrix1")
    matrix_garbage_collector.matrix_service.delete.assert_any_call("matrix2")

    matrix_garbage_collector.dry_run = True
    matrix_garbage_collector.matrix_service.delete.reset_mock()
    matrix_garbage_collector._delete_unused_saved_matrices(unused_matrices)
    matrix_garbage_collector.matrix_service.delete.assert_not_called()


def test_clean_matrices(matrix_garbage_collector: MatrixGarbageCollector) -> None:
    matrix_garbage_collector.matrix_service.get_matrices.return_value = [
        MatrixMetadataDTO(id="matrix2", width=0, height=0, version=0, created_at=datetime(2020, 1, 1, 0, 0, 0))
    ]
    matrix_garbage_collector.matrix_service.get_used_matrices = Mock(
        return_value={MatrixReference(matrix_id="matrix1", use_description="")}
    )
    matrix_garbage_collector._delete_unused_saved_matrices = Mock()

    matrix_garbage_collector.clean_matrices()

    matrix_garbage_collector._delete_unused_saved_matrices.assert_called_once_with(unused_matrices={"matrix2"})


@pytest.mark.parametrize("retention_time, expected_remove", [(-1, True), (3600, False)])
def test_clean_matrices_actual_service(
    matrix_service: MatrixService, retention_time: int, expected_remove: bool
) -> None:
    gc = MatrixGarbageCollector(
        matrix_service=matrix_service, sleeping_time=3600, dry_run=False, retention_time=retention_time
    )

    with db():
        initial_matrices = matrix_service.get_matrices()
        assert initial_matrices == []

        matrix_id = matrix_service.create(pd.DataFrame(data=[[0]]))

        updated_matrices = matrix_service.get_matrices()

        assert [m.id for m in updated_matrices] == [matrix_id]
        gc.clean_matrices()

        matrices_after_clean = matrix_service.get_matrices()
        if expected_remove:
            assert matrices_after_clean == []
        else:
            # Ensures the matrix wasn't deleted as it was created recently
            assert len(matrices_after_clean) == 1


@with_db_context
@with_admin_user
def test_clean_matrices_variant_snapshot(
    empty_study_930: FileStudy, variant_study_service: VariantStudyService
) -> None:
    # Create a real matrix_service
    bucket_dir = (
        variant_study_service.command_factory.command_context.matrix_service.matrix_content_repository.bucket_dir
    )
    matrix_service = MatrixService(
        repo=MatrixRepository(db.session),
        repo_dataset=MatrixDataSetRepository(db.session),
        matrix_content_repository=MatrixContentRepository(bucket_dir, InternalMatrixFormat.TSV),
        file_transfer_manager=Mock(),
        task_service=Mock(),
        config=Mock(),
        user_service=Mock(),
    )
    variant_study_service.command_factory.command_context.matrix_service = matrix_service
    command_context = variant_study_service.command_factory.command_context

    # Create a RawStudy with 1 area and 1 thermal
    study = empty_study_930
    version = study.config.version
    create_area_cmd = CreateArea(area_name="fr", command_context=command_context, study_version=version)
    output = create_area_cmd.apply(study)
    assert output.status
    cmd = CreateCluster(
        area_id="fr",
        parameters=ThermalClusterCreation(name="thermal_cluster", nominal_capacity=1000),
        command_context=command_context,
        study_version=version,
    )
    output = cmd.apply(study)
    assert output.status

    # Add the study in DB
    parent_id = str(uuid.uuid4())
    parent = RawStudy(id=parent_id, name="Parent", path=str(study.config.study_path), version=str(version))
    db.session.add(parent)
    db.session.commit()

    # Create a variant
    variant_study = variant_study_service.create_variant_study(parent_id, "variant_study")

    # Add a GenerateThermalTimeSeries command
    command = GenerateThermalClusterTimeSeries(command_context=command_context, study_version=version).to_dto()
    variant_study_service.append_command(variant_study.id, command)

    # Generate the snapshot
    variant_study_service.get_raw(variant_study)

    # Ensures the matrix created by the `GenerateThermalClusterTimeSeries` command is seen as used.
    # Because it's present in the variant snapshot
    # This way it won't be cleaned by the garbage collector.
    used_matrices = list(matrix_service.get_used_matrices())
    assert len(used_matrices) == 1

    # Clean the snapshot
    variant_study_service.clear_all_snapshots(retention_time=timedelta())

    # Ensures no matrix is used now that the snapshot is cleaned
    used_matrices = list(matrix_service.get_used_matrices())
    assert len(used_matrices) == 0

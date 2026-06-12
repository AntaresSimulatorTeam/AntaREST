# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
import shutil
from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

from antarest.blobstore.service import BlobService
from antarest.core.config import InternalMatrixFormat
from antarest.core.utils.archives import ArchiveFormat, archive_dir
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.repository import MatrixContentRepository, MatrixRepository
from antarest.matrixstore.service import MatrixService
from antarest.output.storage.file.abstract_storage import FileStudyOutputs, IFileOutputsProvider
from antarest.output.storage.file.in_study import InStudyFileOutputStorage
from antarest.study.business.model.thermal_cluster_model import ThermalClusterCreation
from antarest.study.model import DEFAULT_WORKSPACE_NAME, STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy, StudyFactory
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_cluster import CreateCluster
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.conftest import empty_study_fixture
from tests.db_statement_recorder import DBStatementRecorder
from tests.helpers import build_dao_from_file_study, create_raw_study, dirhash, with_db_context
from tests.test_helpers.outputs import create_minimal_output_dir_from_name


def test_export_flat_export_all_files_except_output(
    empty_study_930: FileStudy, raw_study_service: RawStudyService
) -> None:
    study_path = empty_study_930.config.study_path
    tmp_path = study_path.parent

    output_path = study_path / "output"
    output_path.mkdir()
    create_minimal_output_dir_from_name(output_path, "20260219-1111eco")

    # compute hash without outputs
    shutil.copytree(study_path, tmp_path / "copy_without_outputs", ignore=shutil.ignore_patterns("output"))
    hash_without_outputs = dirhash(tmp_path / "copy_without_outputs", "md5")

    # Export should be the same as the one we had without the output dir
    study = create_raw_study(id=empty_study_930.config.study_id, workspace=DEFAULT_WORKSPACE_NAME, path=str(study_path))
    raw_study_service.export_study_flat(study, tmp_path / "export")
    assert not (tmp_path / "export" / "output").exists()
    export_hash = dirhash(tmp_path / "export", "md5")
    assert hash_without_outputs == export_hash


@with_db_context
def test_normalize_denormalized_methods(tmp_path: Path, study_factory: StudyFactory) -> None:
    # Create a real matrix_service with a db connection to test DB queries
    db_session = db.session
    buket_dir = tmp_path / "matrixstore_bucket"
    repo = MatrixRepository(db_session)
    content_repo = MatrixContentRepository(buket_dir, InternalMatrixFormat.FEATHER)
    matrix_service = MatrixService(repo, Mock(), content_repo, Mock(), Mock(), Mock(), Mock())

    # Create a `FileStudy` with this matrix_service
    file_study = empty_study_fixture(STUDY_VERSION_8_8, matrix_service, tmp_path)

    # Create a `RawStudy` object based on the `FileStudy`
    study_path = file_study.config.study_path
    study = create_raw_study(id=file_study.config.study_id, path=str(study_path), workspace=DEFAULT_WORKSPACE_NAME)

    # Use this matrix_service in the raw_study_service and in the command_context
    matrix_constants = GeneratorMatrixConstants(matrix_service)
    matrix_constants.init_constant_matrices()
    blob_service = Mock(spec=BlobService)
    command_context = CommandContext(
        generator_matrix_constants=matrix_constants, matrix_service=matrix_service, blob_service=blob_service
    )
    study_factory._matrix_service = matrix_service
    raw_study_service = RawStudyService(Mock(), study_factory, Mock(), command_context, Mock())
    dao = build_dao_from_file_study(file_study, command_context, True)

    # Create an area and a thermal with specific matrices to have real DB matrices in our study
    version = file_study.config.version
    cmd = CreateArea(command_context=command_context, area_name="fr", study_version=version)
    output = cmd.apply(dao)
    assert output.status
    cmd = CreateCluster(
        area_id="fr",
        parameters=ThermalClusterCreation(name="th1"),
        prepro=8760 * [[2]],
        command_context=command_context,
        study_version=version,
    )
    output = cmd.apply(dao)
    assert output.status

    # Ensures the matrix is normalized for now
    normalized_path = study_path / "input" / "load" / "series" / "load_fr.txt.link"
    denormalized_path = study_path / "input" / "load" / "series" / "load_fr.txt"
    assert normalized_path.exists()
    content = normalized_path.read_text()
    assert not denormalized_path.exists()

    # Normalize the study
    with DBStatementRecorder(db_session.bind) as db_recorder:
        raw_study_service.normalize_study(study)
        assert len(db_recorder.sql_statements) == 0  # no DB request as there is nothing to do

    assert normalized_path.read_text() == content
    assert not denormalized_path.exists()

    # Denormalize the study
    with DBStatementRecorder(db_session.bind) as db_recorder:
        raw_study_service.denormalize_study(study)
        assert len(db_recorder.sql_statements) == 1  # 1 DB request for all matrices

    assert not normalized_path.exists()
    assert denormalized_path.exists()
    dataframe = denormalized_path.read_bytes()

    # Denormalize again
    with DBStatementRecorder(db_session.bind) as db_recorder:
        raw_study_service.denormalize_study(study)
        assert len(db_recorder.sql_statements) == 0  # no DB request as there is nothing to do

    assert not normalized_path.exists()
    assert denormalized_path.exists()
    assert denormalized_path.read_bytes() == dataframe

    # Normalize the study to come back to the initial point
    with DBStatementRecorder(db_session.bind) as db_recorder:
        raw_study_service.normalize_study(study)
        assert len(db_recorder.sql_statements) == 1  # 1 DB request for all matrices

    assert normalized_path.exists()
    assert not denormalized_path.exists()


def test_export_output(tmp_path: Path) -> None:
    output_id = "output_id"
    root = tmp_path / "folder"
    root.mkdir()
    (root / "test").mkdir()
    (root / "test/file.txt").write_text("Bonjour")
    (root / "file.txt").write_text("Hello, World")
    (root / "output" / output_id).mkdir(parents=True)
    (root / "output" / output_id / "file_output.txt").write_text("42")

    export_path = tmp_path / "study.zip"

    study_factory = Mock()

    study = create_raw_study(id="Yo", path=root)
    study_tree = Mock()
    study_factory.create_from_fs.return_value = study_tree

    class OutputsProvider(IFileOutputsProvider):
        def get_outputs(self, study_id: str) -> FileStudyOutputs:
            return FileStudyOutputs(outputs_path=root / "output", study_workspace=DEFAULT_WORKSPACE_NAME)

    output_storage = InStudyFileOutputStorage(
        OutputsProvider(), cache=Mock(), remote_executor=Mock(), repository=Mock()
    )

    output_storage.export_output(study.id, output_id, export_path)
    zipf = ZipFile(export_path)

    assert "file_output.txt" in zipf.namelist()

    # asserts exporting a zipped output doesn't raise an error
    output_path = root / "output" / output_id
    target_path = root / "output" / f"{output_id}.zip"
    archive_dir(output_path, target_path, True, ArchiveFormat.ZIP)
    output_storage.export_output(study.id, output_id, export_path)

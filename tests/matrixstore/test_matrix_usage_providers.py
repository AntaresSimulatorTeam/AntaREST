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
from datetime import datetime
from pathlib import Path

import pytest

from antarest.core.config import DEFAULT_WORKSPACE_NAME
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.model import MatrixReference
from antarest.matrixstore.service import ISimpleMatrixService, MatrixService
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.rawstudy.raw_study_matrix_usage_provider import RawStudyMatrixUsageProvider
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.variantstudy.business.matrix_constants.matrix_constants_usage_provider import (
    ConstantsMatrixUsageProvider,
)
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.command_matrix_usage_provider import CommandMatrixUsageProvider
from antarest.study.storage.variantstudy.model.command.common import CommandName
from antarest.study.storage.variantstudy.model.dbmodel import CommandBlock, VariantStudy
from antarest.study.storage.variantstudy.repository import VariantStudyRepository
from tests.helpers import create_raw_study, with_db_context


@pytest.fixture
@with_db_context
def raw_studies_matrix_usage_provider(raw_study_service: RawStudyService, matrix_service: ISimpleMatrixService):
    return RawStudyMatrixUsageProvider(StudyMetadataRepository(raw_study_service.cache), matrix_service)


@pytest.fixture
def command_matrix_usage_provider(variant_study_repository: VariantStudyRepository, command_factory: CommandFactory):
    command_matrix_usage_provider = CommandMatrixUsageProvider(variant_study_repository, command_factory)

    return command_matrix_usage_provider


@pytest.fixture
def constants_matrix_usage_provider(matrix_service: MatrixService):
    matrix_constants = GeneratorMatrixConstants(matrix_service)
    return ConstantsMatrixUsageProvider(matrix_constants, matrix_service)


def test_raw_studies_matrix_usage_provider(
    raw_studies_matrix_usage_provider: RawStudyMatrixUsageProvider, raw_study_service: RawStudyService, tmp_path
):
    matrix_name1 = "matrix_name1"
    matrix_name2 = "matrix_name2"
    matrix_name3 = "matrix_name3"
    matrix_name4 = "matrix_name4"
    matrices_name = ["matrix_name1", "matrix_name2", "matrix_name3"]

    metadata_raw_study = create_raw_study(
        id="study1",
        workspace=DEFAULT_WORKSPACE_NAME,
        path=str(tmp_path / "studies"),
        version="720",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    with db():
        raw_study = raw_study_service.create(metadata_raw_study)

        (Path(raw_study.path) / f"{matrix_name1}.link").write_text(f"matrix://{matrix_name1}")
        (Path(raw_study.path) / f"{matrix_name2}.link").write_text(f"matrix://{matrix_name2}")
        (Path(raw_study.path) / f"{matrix_name3}.link").write_text(f"matrix://{matrix_name3}")
        (Path(raw_study.path) / f"{matrix_name4}.txt").write_text(f"matrix://{matrix_name4}")

        raw_studies_matrix_usage_provider.study_metadata_repo.save(metadata_raw_study)

        matrices_references = raw_studies_matrix_usage_provider.get_matrix_usage()
        matrices_references_id = [matrix_reference.matrix_id for matrix_reference in matrices_references]
        matrices_references_id.sort()

        assert matrices_name == matrices_references_id


def test_command_matrix_usage_provider(
    command_matrix_usage_provider: CommandMatrixUsageProvider,
    variant_study_repository: VariantStudyRepository,
    tmp_path,
):
    with db():
        study_id = "study_id"

        study_version = "880"
        variant_study_repository.save(VariantStudy(id=study_id, version=study_version, path=tmp_path.as_posix()))
        matrices_id = "a68de4b5e96a60c8ceb3c7b7ef93461725bdbbff3516b136585a743b5c0ec664"
        use_description = f"Used by command {matrices_id} from variant study {study_id}"

        # TODO: add series to the command blocks
        command_block1 = CommandBlock(
            study_id=study_id,
            command=CommandName.CREATE_LINK.value,
            args='{"area1": "area1", "area2": "area2", "series": [[1,2,3]]}',
            index=0,
            version=7,
            study_version=study_version,
        )
        command_block2 = CommandBlock(
            study_id=study_id,
            command=CommandName.CREATE_LINK.value,
            args='{"area1": "area2", "area2": "area3","series": [[1,2,3]]}',
            index=0,
            version=7,
            study_version=study_version,
        )

        db.session.add(command_block1)
        db.session.add(command_block2)
        db.session.commit()

        matrices_references = command_matrix_usage_provider.get_matrix_usage()

        assert matrices_references == [MatrixReference(matrix_id=matrices_id, use_description=use_description)] * 4


def test_constants_matrix_usage_provider(constants_matrix_usage_provider: ConstantsMatrixUsageProvider):
    constant1 = {"c1": "constant_name1"}
    constant2 = {"c2": "constant_name2"}
    constant3 = {"c3": "constant_name3"}
    constant4 = {"c4": "constant_name4"}
    constants = [constant1, constant2, constant3, constant4]

    for constant in constants:
        constants_matrix_usage_provider.matrix_constants.hashes.update(constant)

    constants_reference = constants_matrix_usage_provider.get_matrix_usage()
    matrix_ref_ids = [ref.matrix_id for ref in constants_reference]
    matrix_ref_ids.sort()
    for constant_id, matrix_ref_id in zip(constants, constants_reference):
        assert constant_id, matrix_ref_id

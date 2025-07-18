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

import pytest

from antarest.core.config import Config
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.service import MatrixService
from antarest.study.storage.rawstudy.raw_study_matrix_usage_provider import RawStudyMatrixUsageProvider
from antarest.study.storage.variantstudy.business.matrix_constants.matrix_constants_usage_provider import (
    ConstantsMatrixUsageProvider,
)
from antarest.study.storage.variantstudy.command_matrix_usage_provider import CommandMatrixUsageProvider
from antarest.study.storage.variantstudy.model.command.common import CommandName
from antarest.study.storage.variantstudy.model.dbmodel import CommandBlock, VariantStudy
from antarest.study.storage.variantstudy.repository import VariantStudyRepository


@pytest.fixture
def raw_studies_matrix_usage_provider(core_config: Config, matrix_service: MatrixService):
    return RawStudyMatrixUsageProvider(core_config, matrix_service)


@pytest.fixture
def command_matrix_usage_provider(study_service, matrix_service):
    command_matrix_usage_provider = CommandMatrixUsageProvider(study_service, matrix_service)

    return command_matrix_usage_provider


@pytest.fixture
def constants_matrix_usage_provider(variant_study_service, matrix_service):
    return ConstantsMatrixUsageProvider(variant_study_service, matrix_service)


def test_raw_studies_matrix_usage_provider(raw_studies_matrix_usage_provider):
    matrix_name1 = "matrix_name1"
    matrix_name2 = "matrix_name2"
    matrix_name3 = "matrix_name3"
    matrix_name4 = "matrix_name4"
    matrices_name = ["matrix_name1", "matrix_name2", "matrix_name3"]

    raw_study_path = raw_studies_matrix_usage_provider.managed_studies_path
    raw_study_path.mkdir()
    (raw_study_path / f"{matrix_name1}.link").write_text(f"matrix://{matrix_name1}")
    (raw_study_path / f"{matrix_name2}.link").write_text(f"matrix://{matrix_name2}")
    (raw_study_path / f"{matrix_name3}.link").write_text(f"matrix://{matrix_name3}")
    (raw_study_path / f"{matrix_name4}.txt").write_text(f"matrix://{matrix_name4}")

    matrices_references = raw_studies_matrix_usage_provider.get_matrix_usage()
    matrices_references_id = [matrix_reference.matrix_id for matrix_reference in matrices_references]
    matrices_references_id.sort()
    assert len(matrices_references) == 3

    for matrix_name, matrix_id in zip(matrices_name, matrices_references_id):
        assert matrix_name == matrix_id


def test_command_matrix_usage_provider(
    command_matrix_usage_provider: CommandMatrixUsageProvider, variant_study_repository: VariantStudyRepository
):
    with db():
        study_id = "study_id"

        study_version = "880"
        variant_study_repository.save(VariantStudy(id=study_id, version=study_version))
        matrices_id = "a68de4b5e96a60c8ceb3c7b7ef93461725bdbbff3516b136585a743b5c0ec664"
        use_description = f"Used by {matrices_id} from study {study_id}"

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

        assert len(matrices_references) == 4

        for matrix_ref in matrices_references:
            assert matrix_ref.matrix_id == matrices_id
            assert matrix_ref.use_description == use_description


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

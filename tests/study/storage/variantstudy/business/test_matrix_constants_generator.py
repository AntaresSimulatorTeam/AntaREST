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

import numpy as np

from antarest.core.config import InternalMatrixFormat
from antarest.matrixstore.repository import MatrixContentRepository
from antarest.matrixstore.service import SimpleMatrixService
from antarest.study.storage.variantstudy.business import matrix_constants
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    MATRIX_PROTOCOL_PREFIX,
    GeneratorMatrixConstants,
)

DEFAULT_INTERNAL_FORMAT = InternalMatrixFormat.TSV


class TestGeneratorMatrixConstants:
    def test_get_st_storage(self, tmp_path):
        matrix_content_repository = MatrixContentRepository(bucket_dir=tmp_path, format=DEFAULT_INTERNAL_FORMAT)
        generator = GeneratorMatrixConstants(
            matrix_service=SimpleMatrixService(
                matrix_content_repository=matrix_content_repository,
            )
        )
        generator.init_constant_matrices()

        ref1 = generator.get_st_storage_pmax_injection()
        matrix_id1 = ref1.split(MATRIX_PROTOCOL_PREFIX)[1]
        matrix_dto1 = generator.matrix_service.get(matrix_id1)
        assert np.array(matrix_dto1.data).all() == matrix_constants.st_storage.series.pmax_injection.all()

        ref2 = generator.get_st_storage_pmax_withdrawal()
        matrix_id2 = ref2.split(MATRIX_PROTOCOL_PREFIX)[1]
        matrix_dto2 = generator.matrix_service.get(matrix_id2)
        assert np.array(matrix_dto2.data).all() == matrix_constants.st_storage.series.pmax_withdrawal.all()

        ref3 = generator.get_st_storage_lower_rule_curve()
        matrix_id3 = ref3.split(MATRIX_PROTOCOL_PREFIX)[1]
        matrix_dto3 = generator.matrix_service.get(matrix_id3)
        assert np.array(matrix_dto3.data).all() == matrix_constants.st_storage.series.lower_rule_curve.all()

        ref4 = generator.get_st_storage_upper_rule_curve()
        matrix_id4 = ref4.split(MATRIX_PROTOCOL_PREFIX)[1]
        matrix_dto4 = generator.matrix_service.get(matrix_id4)
        assert np.array(matrix_dto4.data).all() == matrix_constants.st_storage.series.upper_rule_curve.all()

        ref5 = generator.get_st_storage_inflows()
        matrix_id5 = ref5.split(MATRIX_PROTOCOL_PREFIX)[1]
        matrix_dto5 = generator.matrix_service.get(matrix_id5)
        assert np.array(matrix_dto5.data).all() == matrix_constants.st_storage.series.inflows.all()

    def test_get_binding_constraint_before_v87(self, tmp_path):
        matrix_content_repository = MatrixContentRepository(bucket_dir=tmp_path, format=DEFAULT_INTERNAL_FORMAT)
        generator = GeneratorMatrixConstants(
            matrix_service=SimpleMatrixService(
                matrix_content_repository=matrix_content_repository,
            )
        )
        generator.init_constant_matrices()
        series = matrix_constants.binding_constraint.series_before_v87

        hourly = generator.get_binding_constraint_hourly_86()
        hourly_matrix_id = hourly.split(MATRIX_PROTOCOL_PREFIX)[1]
        hourly_matrix_dto = generator.matrix_service.get(hourly_matrix_id)
        assert np.array(hourly_matrix_dto.data).all() == series.default_bc_hourly.all()

        daily_weekly = generator.get_binding_constraint_daily_weekly_86()
        matrix_id = daily_weekly.split(MATRIX_PROTOCOL_PREFIX)[1]
        matrix_dto = generator.matrix_service.get(matrix_id)
        assert np.array(matrix_dto.data).all() == series.default_bc_weekly_daily.all()

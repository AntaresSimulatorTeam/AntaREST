from typing import Dict

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.service import MatrixService
from antarest.study.storage.variantstudy.business import matrix_constants
from antarest.study.storage.variantstudy.business.matrix_constants.common import (
    NULL_MATRIX,
)

# TODO: put index into variable
HYDRO_COMMON_CAPACITY_MAX_POWER_V7 = "hydro/common/capacity/max_power/v7"
HYDRO_COMMON_CAPACITY_RESERVOIR_V7 = "hydro/common/capacity/reservoir/v7"
HYDRO_COMMON_CAPACITY_RESERVOIR_V6 = "hydro/common/capacity/reservoir/v6"
HYDRO_COMMON_CAPACITY_INFLOW_PATTERN = "hydro/common/capacity/inflow_pattern"
HYDRO_COMMON_CAPACITY_CREDIT_MODULATION = (
    "hydro/common/capacity/credit_modulations"
)
PREPRO_CONVERSION = "prepro/conversion"
PREPRO_DATA = "prepro/data"
NULL_MATRIX_NAME = "null_matrix"
MATRIX_PROTOCOL_PREFIX = "matrix://"


class GeneratorMatrixConstants:
    def __init__(self, matrix_service: MatrixService) -> None:
        self.hashes: Dict[str, str] = {}
        self.matrix_service: MatrixService = matrix_service
        self._init()

    def _init(self) -> None:
        with db():
            self.hashes[
                HYDRO_COMMON_CAPACITY_MAX_POWER_V7
            ] = self.matrix_service.create(matrix_constants.hydro.v7.max_power)
            self.hashes[
                HYDRO_COMMON_CAPACITY_RESERVOIR_V7
            ] = self.matrix_service.create(matrix_constants.hydro.v7.reservoir)
            self.hashes[
                HYDRO_COMMON_CAPACITY_RESERVOIR_V6
            ] = self.matrix_service.create(matrix_constants.hydro.v6.reservoir)
            self.hashes[
                HYDRO_COMMON_CAPACITY_INFLOW_PATTERN
            ] = self.matrix_service.create(
                matrix_constants.hydro.v7.inflow_pattern
            )
            self.hashes[
                HYDRO_COMMON_CAPACITY_CREDIT_MODULATION
            ] = self.matrix_service.create(
                matrix_constants.hydro.v7.credit_modulations
            )
            self.hashes[PREPRO_CONVERSION] = self.matrix_service.create(
                matrix_constants.prepro.conversion
            )
            self.hashes[PREPRO_DATA] = self.matrix_service.create(
                matrix_constants.prepro.data
            )

            self.hashes[NULL_MATRIX_NAME] = self.matrix_service.create(
                NULL_MATRIX
            )

    def get_hydro_max_power(self, version: int) -> str:
        if version > 650:
            return (
                MATRIX_PROTOCOL_PREFIX
                + self.hashes[HYDRO_COMMON_CAPACITY_MAX_POWER_V7]
            )
        else:
            return MATRIX_PROTOCOL_PREFIX + self.hashes[NULL_MATRIX_NAME]

    def get_hydro_reservoir(self, version: int) -> str:
        if version > 650:
            return (
                MATRIX_PROTOCOL_PREFIX
                + self.hashes[HYDRO_COMMON_CAPACITY_RESERVOIR_V7]
            )
        return (
            MATRIX_PROTOCOL_PREFIX
            + self.hashes[HYDRO_COMMON_CAPACITY_RESERVOIR_V6]
        )

    def get_hydro_credit_modulations(self) -> str:
        return (
            MATRIX_PROTOCOL_PREFIX
            + self.hashes[HYDRO_COMMON_CAPACITY_CREDIT_MODULATION]
        )

    def get_hydro_inflow_pattern(self) -> str:
        return (
            MATRIX_PROTOCOL_PREFIX
            + self.hashes[HYDRO_COMMON_CAPACITY_INFLOW_PATTERN]
        )

    def get_prepro_conversion(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[PREPRO_CONVERSION]

    def get_prepro_data(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[PREPRO_DATA]

    def get_null_matrix(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[NULL_MATRIX_NAME]

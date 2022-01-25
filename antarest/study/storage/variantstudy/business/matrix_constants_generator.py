from typing import Dict

from filelock import FileLock

from antarest.matrixstore.service import ISimpleMatrixService
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
THERMAL_PREPRO_DATA = "thermals/prepro/data"
THERMAL_PREPRO_MODULATION = "thermals/prepro/modulation"
LINK_V7 = "link_v7"
LINK_V8 = "link_v8"
NULL_MATRIX_NAME = "null_matrix"
MATRIX_PROTOCOL_PREFIX = "matrix://"


class GeneratorMatrixConstants:
    def __init__(self, matrix_service: ISimpleMatrixService) -> None:
        self.hashes: Dict[str, str] = {}
        self.matrix_service: ISimpleMatrixService = matrix_service
        with FileLock("matrix_constant_init.lock"):
            self._init()

    def _init(self) -> None:
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
        self.hashes[THERMAL_PREPRO_DATA] = self.matrix_service.create(
            matrix_constants.thermals.prepro.data
        )

        self.hashes[THERMAL_PREPRO_MODULATION] = self.matrix_service.create(
            matrix_constants.thermals.prepro.modulation
        )
        self.hashes[LINK_V7] = self.matrix_service.create(
            matrix_constants.link.v7.link
        )
        self.hashes[LINK_V8] = self.matrix_service.create(
            matrix_constants.link.v8.link
        )

        self.hashes[NULL_MATRIX_NAME] = self.matrix_service.create(NULL_MATRIX)

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

    def get_thermal_prepro_data(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[THERMAL_PREPRO_DATA]

    def get_thermal_prepro_modulation(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[THERMAL_PREPRO_MODULATION]

    def get_link(self, version: int) -> str:
        if version < 820:
            return MATRIX_PROTOCOL_PREFIX + self.hashes[LINK_V7]
        return MATRIX_PROTOCOL_PREFIX + self.hashes[LINK_V8]

    def get_null_matrix(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[NULL_MATRIX_NAME]

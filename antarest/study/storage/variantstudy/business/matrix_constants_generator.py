import tempfile
from pathlib import Path
from typing import Dict

from filelock import FileLock

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.storage.variantstudy.business import matrix_constants
from antarest.study.storage.variantstudy.business.matrix_constants.common import (
    FIXED_4_COLUMNS,
    FIXED_8_COLUMNS,
    NULL_MATRIX,
    NULL_SCENARIO_MATRIX,
)

# TODO: put index into variable

HYDRO_COMMON_CAPACITY_MAX_POWER_V7 = "hydro/common/capacity/max_power/v7"
HYDRO_COMMON_CAPACITY_RESERVOIR_V7 = "hydro/common/capacity/reservoir/v7"
HYDRO_COMMON_CAPACITY_RESERVOIR_V6 = "hydro/common/capacity/reservoir/v6"
HYDRO_COMMON_CAPACITY_INFLOW_PATTERN = "hydro/common/capacity/inflow_pattern"
HYDRO_COMMON_CAPACITY_CREDIT_MODULATION = "hydro/common/capacity/credit_modulations"
RESERVES_TS = "reserves"
MISCGEN_TS = "miscgen"
PREPRO_CONVERSION = "prepro/conversion"
PREPRO_DATA = "prepro/data"
THERMAL_PREPRO_DATA = "thermals/prepro/data"
THERMAL_PREPRO_MODULATION = "thermals/prepro/modulation"
LINK_V7 = "link_v7"
LINK_V8 = "link_v8"
LINK_DIRECT = "link_direct"
LINK_INDIRECT = "link_indirect"
NULL_MATRIX_NAME = "null_matrix"
EMPTY_SCENARIO_MATRIX = "empty_scenario_matrix"
ONES_SCENARIO_MATRIX = "ones_scenario_matrix"


# Short-term storage aliases
ST_STORAGE_PMAX_INJECTION = ONES_SCENARIO_MATRIX
ST_STORAGE_PMAX_WITHDRAWAL = ONES_SCENARIO_MATRIX
ST_STORAGE_LOWER_RULE_CURVE = EMPTY_SCENARIO_MATRIX
ST_STORAGE_UPPER_RULE_CURVE = ONES_SCENARIO_MATRIX
ST_STORAGE_INFLOWS = EMPTY_SCENARIO_MATRIX

MATRIX_PROTOCOL_PREFIX = "matrix://"


# noinspection SpellCheckingInspection
class GeneratorMatrixConstants:
    def __init__(self, matrix_service: ISimpleMatrixService) -> None:
        self.hashes: Dict[str, str] = {}
        self.matrix_service: ISimpleMatrixService = matrix_service
        with FileLock(
            str(Path(tempfile.gettempdir()) / "matrix_constant_init.lock")
        ):
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
        self.hashes[LINK_DIRECT] = self.matrix_service.create(
            matrix_constants.link.v8.direct
        )
        self.hashes[LINK_INDIRECT] = self.matrix_service.create(
            matrix_constants.link.v8.indirect
        )

        self.hashes[NULL_MATRIX_NAME] = self.matrix_service.create(NULL_MATRIX)
        self.hashes[EMPTY_SCENARIO_MATRIX] = self.matrix_service.create(
            NULL_SCENARIO_MATRIX
        )
        self.hashes[RESERVES_TS] = self.matrix_service.create(FIXED_4_COLUMNS)
        self.hashes[MISCGEN_TS] = self.matrix_service.create(FIXED_8_COLUMNS)

        # Some short-term storage matrices use np.ones((8760, 1))
        self.hashes[ONES_SCENARIO_MATRIX] = self.matrix_service.create(
            matrix_constants.st_storage.series.pmax_injection
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

    def get_thermal_prepro_data(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[THERMAL_PREPRO_DATA]

    def get_thermal_prepro_modulation(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[THERMAL_PREPRO_MODULATION]

    def get_link(self, version: int) -> str:
        if version < 820:
            return MATRIX_PROTOCOL_PREFIX + self.hashes[LINK_V7]
        return MATRIX_PROTOCOL_PREFIX + self.hashes[LINK_V8]

    def get_link_direct(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[LINK_DIRECT]

    def get_link_indirect(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[LINK_INDIRECT]

    def get_null_matrix(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[NULL_MATRIX_NAME]

    def get_null_scenario_matrix(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[EMPTY_SCENARIO_MATRIX]

    def get_default_reserves(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[RESERVES_TS]

    def get_default_miscgen(self) -> str:
        return MATRIX_PROTOCOL_PREFIX + self.hashes[MISCGEN_TS]

    
    def get_st_storage_pmax_injection(self) -> str:
        """2D-matrix of shape (8760, 1), filled-in with ones."""
        return MATRIX_PROTOCOL_PREFIX + self.hashes[ST_STORAGE_PMAX_INJECTION]

    def get_st_storage_pmax_withdrawal(self) -> str:
        """2D-matrix of shape (8760, 1), filled-in with ones."""
        return MATRIX_PROTOCOL_PREFIX + self.hashes[ST_STORAGE_PMAX_WITHDRAWAL]

    def get_st_storage_lower_rule_curve(self) -> str:
        """2D-matrix of shape (8760, 1), filled-in with zeros."""
        return MATRIX_PROTOCOL_PREFIX + self.hashes[ST_STORAGE_LOWER_RULE_CURVE]

    def get_st_storage_upper_rule_curve(self) -> str:
        """2D-matrix of shape (8760, 1), filled-in with ones."""
        return MATRIX_PROTOCOL_PREFIX + self.hashes[ST_STORAGE_UPPER_RULE_CURVE]

    def get_st_storage_inflows(self) -> str:
        """2D-matrix of shape (8760, 1), filled-in with zeros."""
        return MATRIX_PROTOCOL_PREFIX + self.hashes[ST_STORAGE_INFLOWS]
    

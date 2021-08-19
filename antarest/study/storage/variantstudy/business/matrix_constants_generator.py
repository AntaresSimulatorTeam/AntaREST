from typing import Dict

from antarest.matrixstore.service import MatrixService
from antarest.study.storage.variantstudy.business import matrix_constants
from antarest.study.storage.variantstudy.business.matrix_constants.common import (
    NULL_MATRIX,
)


class GeneratorMatrixConstants:
    def __init__(self, matrix_service: MatrixService):
        self.hashes: Dict[str, str] = {}
        self.matrix_service = matrix_service
        self._init()

    def _init(self):

        self.hashes[
            "hydro/common/capacity/max_power/v7"
        ] = self.matrix_service.create(matrix_constants.hydro.v7.max_power)
        self.hashes[
            "hydro/common/capacity/reservoir/v7"
        ] = self.matrix_service.create(matrix_constants.hydro.v7.reservoir)
        self.hashes[
            "hydro/common/capacity/reservoir/v6"
        ] = self.matrix_service.create(matrix_constants.hydro.v6.reservoir)
        self.hashes[
            "hydro/common/capacity/inflow_pattern"
        ] = self.matrix_service.create(
            matrix_constants.hydro.v7.inflow_pattern
        )
        self.hashes[
            "hydro/common/capacity/credit_modulations"
        ] = self.matrix_service.create(
            matrix_constants.hydro.v7.credit_modulations
        )
        self.hashes["prepro/conversion"] = self.matrix_service.create(
            matrix_constants.prepro.conversion
        )
        self.hashes["prepro/data"] = self.matrix_service.create(
            matrix_constants.prepro.data
        )

        self.hashes["null_matrix"] = self.matrix_service.create(NULL_MATRIX)

    def get_hydro_max_power(self, version: int):
        if version > 650:
            return self.hashes[f"hydro/common/capacity/max_power/v7"]
        else:
            return self.hashes["null_matrix"]

    def get_hydro_reservoir(self, version: int):
        v = "v6"
        if version > 650:
            v = "v7"
        return self.hashes[f"hydro/common/capacity/reservoir/{v}"]

    def get_hydro_credit_modulations(self):
        return self.hashes["hydro/common/capacity/credit_modulations"]

    def get_hydro_inflow_pattern(self):
        return self.hashes["hydro/common/capacity/inflow_pattern"]

    def get_prepro_conversion(self):
        return self.hashes["prepro/conversion"]

    def get_prepro_data(self):
        return self.hashes["prepro/data"]

    def get_null_matrix(self):
        return self.hashes["null_matrix"]

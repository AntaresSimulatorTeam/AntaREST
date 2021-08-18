from typing import Dict

from antarest.matrixstore.service import MatrixService
from antarest.study.storage.variantstudy.business import matrix_constants


class GeneratorMatrixConstants:
    def __init__(self, matrix_service: MatrixService):
        self.hashes: Dict[str, Dict[str, str]] = {"v6": {}, "v7": {}}
        self.matrix_service = matrix_service
        self._init()

    def _init(self):
        self.hashes["v6"][
            "hydro/common/capacity/max_power"
        ] = self.matrix_service.create(matrix_constants.hydro.v6.max_power)
        self.hashes["v6"][
            "hydro/common/capacity/reservoir"
        ] = self.matrix_service.create(matrix_constants.hydro.v6.reservoir)
        self.hashes["v7"][
            "hydro/common/capacity/max_power"
        ] = self.matrix_service.create(matrix_constants.hydro.v7.max_power)
        self.hashes["v7"][
            "hydro/common/capacity/reservoir"
        ] = self.matrix_service.create(matrix_constants.hydro.v7.reservoir)
        self.hashes["v7"][
            "hydro/common/capacity/inflow_pattern"
        ] = self.matrix_service.create(
            matrix_constants.hydro.v7.inflow_pattern
        )
        self.hashes["v7"][
            "hydro/common/capacity/credit_modulations"
        ] = self.matrix_service.create(
            matrix_constants.hydro.v7.credit_modulations
        )
        self.hashes["v7"][
            "hydro/common/capacity/water_values"
        ] = self.matrix_service.create(matrix_constants.hydro.v7.water_values)

    def get_hydro_max_power(self, version: int):
        v = "v6"
        if version > 650:
            v = "v7"
        return self.hashes[v]["hydro/common/capacity/max_power"]

    def get_hydro_reservoir(self, version: int):
        v = "v6"
        if version > 650:
            v = "v7"
        return self.hashes[v]["hydro/common/capacity/reservoir"]

    def get_hydro_credit_modulations(self):
        return self.hashes["v7"]["hydro/common/capacity/credit_modulations"]

    def get_hydro_inflow_pattern(self):
        return self.hashes["v7"]["hydro/common/capacity/inflow_pattern"]

    def get_hydro_credit_water_values(self):
        return self.hashes["v7"]["hydro/common/capacity/water_values"]

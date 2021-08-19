from typing import Dict

from antarest.matrixstore.service import MatrixService
from antarest.study.storage.variantstudy.business import matrix_constants
from antarest.study.storage.variantstudy.business.matrix_constants.common import (
    NULL_MATRIX,
)


class GeneratorMatrixConstants:
    def __init__(self, matrix_service: MatrixService):
        self.hashes: Dict[str, Dict[str, str]] = {"v6": {}, "v7": {}}
        self.matrix_service = matrix_service
        self._init()

    def _init(self):
        self.hashes["v6"][
            "hydro/common/capacity/reservoir"
        ] = self.matrix_service.create(matrix_constants.hydro.v6.reservoir)
        self.hashes["v6"][
            "load/prepro/area_name/conversion"
        ] = self.matrix_service.create(matrix_constants.load.v6.conversion)
        self.hashes["v6"][
            "load/prepro/area_name/data"
        ] = self.matrix_service.create(matrix_constants.load.v6.data)
        self.hashes["v6"][
            "solar/prepro/area_name/conversion"
        ] = self.matrix_service.create(matrix_constants.solar.v6.conversion)
        self.hashes["v6"][
            "solar/prepro/area_name/data"
        ] = self.matrix_service.create(matrix_constants.solar.v6.data)
        self.hashes["v6"][
            "wind/prepro/area_name/conversion"
        ] = self.matrix_service.create(matrix_constants.wind.v6.conversion)
        self.hashes["v6"][
            "wind/prepro/area_name/data"
        ] = self.matrix_service.create(matrix_constants.wind.v6.data)

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

    def get_hydro_max_power(self, version: int):
        v = "v6"
        if version > 650:
            v = "v7"
        return self.hashes[v].get(
            "hydro/common/capacity/max_power",
            self.matrix_service.create(NULL_MATRIX),
        )

    def get_hydro_reservoir(self, version: int):
        v = "v6"
        if version > 650:
            v = "v7"
        return self.hashes[v].get(
            "hydro/common/capacity/reservoir",
            self.matrix_service.create(NULL_MATRIX),
        )

    def get_hydro_credit_modulations(self):
        return self.hashes["v7"].get(
            "hydro/common/capacity/credit_modulations",
            self.matrix_service.create(NULL_MATRIX),
        )

    def get_hydro_inflow_pattern(self):
        return self.hashes["v7"].get(
            "hydro/common/capacity/inflow_pattern",
            self.matrix_service.create(NULL_MATRIX),
        )

    def get_hydro_water_values(self):
        return self.hashes["v7"].get(
            "hydro/common/capacity/water_values",
            self.matrix_service.create(NULL_MATRIX),
        )

    def get_hydro_energy(self):
        return self.hashes["v6"].get(
            "hydro/prepro/area_name/energy",
            self.matrix_service.create(NULL_MATRIX),
        )

    def get_hydro_series_mod(self):
        return self.hashes["v6"].get(
            "hydro/series/area_name/mod",
            self.matrix_service.create(NULL_MATRIX),
        )

    def get_hydro_series_ror(self):
        return self.hashes["v6"].get(
            "hydro/series/area_name/ror",
            self.matrix_service.create(NULL_MATRIX),
        )

    def get_load_prepro_conversion(self):
        return self.hashes["v6"].get(
            "load/prepro/area_name/conversion",
            self.matrix_service.create(NULL_MATRIX),
        )

    def get_load_prepro_data(self):
        return self.hashes["v6"].get(
            "load/prepro/area_name/data",
            self.matrix_service.create(NULL_MATRIX),
        )

    def get_load_prepro_k(self):
        return self.hashes["v6"].get(
            "load/prepro/area_name/k", self.matrix_service.create(NULL_MATRIX)
        )

    def get_load_prepro_translation(self):
        return self.hashes["v6"].get(
            "load/prepro/area_name/translation",
            self.matrix_service.create(NULL_MATRIX),
        )

    def get_load_series_load_area_name(self):
        return self.hashes["v6"].get(
            "load/series/load_area_name",
            self.matrix_service.create(NULL_MATRIX),
        )

    def get_misc_gen(self):
        return self.hashes["v6"].get(
            "miscgen_area_name",
            self.matrix_service.create(NULL_MATRIX),
        )

    def get_reserves(self):
        return self.hashes["v6"].get(
            "reserves/area_name",
            self.matrix_service.create(NULL_MATRIX),
        )

    def get_solar_prepro_conversion(self):
        return self.hashes["v6"].get(
            "solar/area_name/conversion",
            self.matrix_service.create(NULL_MATRIX),
        )

    def get_solar_prepro_data(self):
        return self.hashes["v6"].get(
            "solar/prepro/area_name/data",
            self.matrix_service.create(NULL_MATRIX),
        )

    def get_solar_prepro_k(self):
        return self.hashes["v6"].get(
            "solar/prepro/area_name/k", self.matrix_service.create(NULL_MATRIX)
        )

    def get_solar_prepro_translation(self):
        return self.hashes["v6"].get(
            "solar/prepro/area_name/translation",
            self.matrix_service.create(NULL_MATRIX),
        )

    def get_solar_series_load_area_name(self):
        return self.hashes["v6"].get(
            "solar/series/load_area_name",
            self.matrix_service.create(NULL_MATRIX),
        )

    def get_wind_prepro_conversion(self):
        return self.hashes["v6"].get(
            "wind/area_name/conversion",
            self.matrix_service.create(NULL_MATRIX),
        )

    def get_wind_prepro_data(self):
        return self.hashes["v6"].get(
            "wind/prepro/area_name/data",
            self.matrix_service.create(NULL_MATRIX),
        )

    def get_wind_prepro_k(self):
        return self.hashes["v6"].get(
            "wind/prepro/area_name/k", self.matrix_service.create(NULL_MATRIX)
        )

    def get_wind_prepro_translation(self):
        return self.hashes["v6"].get(
            "wind/prepro/area_name/translation",
            self.matrix_service.create(NULL_MATRIX),
        )

    def get_wind_series_load_area_name(self):
        return self.hashes["v6"].get(
            "wind/series/load_area_name",
            self.matrix_service.create(NULL_MATRIX),
        )

import typing as t

import numpy as np
from antares.tsgen.duration_generator import ProbabilityLaw
from antares.tsgen.random_generator import MersenneTwisterRNG
from antares.tsgen.ts_generator import ThermalCluster, ThermalDataGenerator

from antarest.study.storage.rawstudy.model.filesystem.config.model import Area, FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import LocalTSGenerationBehavior
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand, OutputTuple
from antarest.study.storage.variantstudy.model.model import CommandDTO


class GenerateThermalClusterTimeSeries(ICommand):
    """
    Command used to generate thermal cluster timeseries for an entire study
    """

    command_name = CommandName.GENERATE_THERMAL_CLUSTER_TIMESERIES
    version = 1

    nb_years: int

    _INNER_MATRICES: t.List[str] = []

    def _apply_config(self, study_data: FileStudyTreeConfig) -> OutputTuple:
        return CommandOutput(status=True, message="Nothing to do"), {}

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        # 1- Get the seed
        default_seed = (
            3005489  # todo: Wait for Florian: Default value in antares-timeseries-generation: 5489. Should we use it ?
        )
        try:
            thermal_seed: int = study_data.tree.get(["settings", "generaldata", "seeds - Mersenne Twister", "seed-tsgen-thermal"])  # type: ignore
        except KeyError:
            thermal_seed = default_seed

        # 2- Loop through areas in alphabetical order
        areas: t.Dict[str, Area] = study_data.config.areas
        sorted_areas = {k: areas[k] for k in sorted(areas)}
        for area_id, area in sorted_areas.items():
            # 3- Loop through thermal clusters in alphabetical order
            sorted_thermals = sorted(area.thermals, key=lambda x: x.id)
            for thermal in sorted_thermals:
                # 4 - Filters out clusters with no generation
                if thermal.gen_ts == LocalTSGenerationBehavior.FORCE_NO_GENERATION:
                    continue
                # 5 - Build the generator
                # todo: I didn't understand if we need a global Generator or one for each cluster.
                rng = MersenneTwisterRNG(seed=thermal_seed)
                generator = ThermalDataGenerator(rng=rng, days=365)
                # todo: Wait for Florian to know if we should use 366 in case of a leap-year study.
                # 6- Build the cluster
                modulation_matrix = study_data.tree.get(
                    ["input", "thermal", "prepro", area_id, thermal.id.lower(), "modulation"]
                )["data"]
                modulation_capacity = np.array([row[2] for row in modulation_matrix])
                ts_generator_matrix = study_data.tree.get(
                    ["input", "thermal", "prepro", area_id, thermal.id.lower(), "data"]
                )["data"]
                fo_duration, po_duration, fo_rate, po_rate, npo_min, npo_max = [
                    np.array(col) for col in zip(*ts_generator_matrix)
                ]
                cluster = ThermalCluster(
                    unit_count=thermal.unit_count,
                    nominal_power=thermal.nominal_capacity,
                    modulation=modulation_capacity,
                    fo_law=ProbabilityLaw(thermal.law_forced.value),
                    fo_volatility=thermal.volatility_forced,
                    po_law=ProbabilityLaw(thermal.law_planned.value),
                    po_volatility=thermal.volatility_planned,
                    fo_duration=fo_duration,
                    fo_rate=fo_rate,
                    po_duration=po_duration,
                    po_rate=po_rate,
                    npo_min=npo_min,
                    npo_max=npo_max,
                )
                # 7- Generate the time-series
                results = generator.generate_time_series(cluster, self.nb_years)
                generated_matrix = results.available_power.tolist()
                # 8- Generates the UUID for the `get_inner_matrices` method
                uuid = study_data.tree.context.matrix.create(generated_matrix)
                self._INNER_MATRICES.append(uuid)
                # 9- Write the matrix inside the input folder.
                matrix_path = ["input", "thermal", "series", area_id, thermal.id.lower(), "series"]
                study_data.tree.save(generated_matrix, matrix_path)
        return CommandOutput(status=True, message="All time series were generated successfully")

    def to_dto(self) -> CommandDTO:
        return CommandDTO(action=self.command_name.value, args={"nb_years": self.nb_years})

    def match_signature(self) -> str:
        return str(self.command_name.value + MATCH_SIGNATURE_SEPARATOR + str(self.nb_years))

    def match(self, other: "ICommand", equal: bool = False) -> bool:
        # Only used inside the cli app that no one uses I believe.
        if not isinstance(other, GenerateThermalClusterTimeSeries):
            return False
        return self.nb_years == other.nb_years

    def _create_diff(self, other: "ICommand") -> t.List["ICommand"]:
        # Only used inside the cli app that no one uses I believe.
        raise NotImplementedError()

    def get_inner_matrices(self) -> t.List[str]:
        # This is used to get used matrices and not remove them inside the garbage collector loop.
        return self._INNER_MATRICES

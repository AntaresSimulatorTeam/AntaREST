import logging
import shutil
import tempfile
import typing as t
from pathlib import Path

import numpy as np
import pandas as pd
from antares.tsgen.duration_generator import ProbabilityLaw
from antares.tsgen.random_generator import MersenneTwisterRNG
from antares.tsgen.ts_generator import ThermalCluster, ThermalDataGenerator

from antarest.study.storage.rawstudy.model.filesystem.config.model import Area, FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import LocalTSGenerationBehavior
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand, OutputTuple
from antarest.study.storage.variantstudy.model.model import CommandDTO

logger = logging.getLogger(__name__)


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
        study_path = study_data.config.study_path
        with tempfile.TemporaryDirectory(
            suffix=".thermal_timeseries_gen.tmp", prefix="~", dir=study_path.parent
        ) as path:
            tmp_dir = Path(path)
            try:
                shutil.copytree(study_path / "input" / "thermal" / "series", tmp_dir, dirs_exist_ok=True)
                self._build_timeseries(study_data, tmp_dir)
            except Exception as e:
                logger.error(f"Unhandled exception when trying to generate thermal timeseries: {e}", exc_info=True)
                raise
            else:
                self._replace_safely_original_files(study_path, tmp_dir)
                return CommandOutput(status=True, message="All time series were generated successfully")

    def _build_timeseries(self, study_data: FileStudy, tmp_path: Path) -> None:
        # 1- Get the seed
        default_seed = 3005489  # NB: Default value in package: 5489, default seed in web: 3005489.
        try:
            thermal_seed: int = study_data.tree.get(["settings", "generaldata", "seeds - Mersenne Twister", "seed-tsgen-thermal"])  # type: ignore
        except KeyError:
            thermal_seed = default_seed

        # 2 - Build the generator
        rng = MersenneTwisterRNG(seed=thermal_seed)
        generator = ThermalDataGenerator(rng=rng, days=365)
        # 3- Loop through areas in alphabetical order
        areas: t.Dict[str, Area] = study_data.config.areas
        sorted_areas = {k: areas[k] for k in sorted(areas)}
        for area_id, area in sorted_areas.items():
            # 4- Loop through thermal clusters in alphabetical order
            sorted_thermals = sorted(area.thermals, key=lambda x: x.id)
            for thermal in sorted_thermals:
                # 5 - Filters out clusters with no generation
                if thermal.gen_ts == LocalTSGenerationBehavior.FORCE_NO_GENERATION:
                    continue
                # 6- Build the cluster
                modulation_matrix = study_data.tree.get(
                    ["input", "thermal", "prepro", area_id, thermal.id.lower(), "modulation"]
                )["data"]
                modulation_capacity = np.array([row[2] for row in modulation_matrix])
                ts_generator_matrix = study_data.tree.get(
                    ["input", "thermal", "prepro", area_id, thermal.id.lower(), "data"]
                )["data"]
                fo_duration, po_duration, fo_rate, po_rate, npo_min, npo_max = [
                    np.array(col, dtype=int) if i not in [2, 3] else np.array(col, dtype=float)
                    for i, col in enumerate(zip(*ts_generator_matrix))
                ]
                cluster = ThermalCluster(
                    unit_count=thermal.unit_count,
                    nominal_power=thermal.nominal_capacity,
                    modulation=modulation_capacity,
                    fo_law=ProbabilityLaw(thermal.law_forced.value.upper()),
                    fo_volatility=thermal.volatility_forced,
                    po_law=ProbabilityLaw(thermal.law_planned.value.upper()),
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
                generated_matrix = results.available_power.T.tolist()
                # 8- Generates the UUID for the `get_inner_matrices` method
                uuid = study_data.tree.context.matrix.create(generated_matrix)
                self._INNER_MATRICES.append(uuid)
                # 9- Write the matrix inside the input folder.
                df = pd.DataFrame(data=generated_matrix, dtype=int)
                target_path = self._build_matrix_path(tmp_path / area_id / thermal.id.lower())
                df.to_csv(target_path, sep="\t", header=False, index=False)

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

    @staticmethod
    def _replace_safely_original_files(study_path: Path, tmp_path: Path) -> None:
        backup_dir = Path(
            tempfile.mkdtemp(
                suffix=".backup_timeseries_generation.tmp",
                prefix="~",
                dir=study_path.parent,
            )
        )
        backup_dir.rmdir()
        original_path = study_path / "input" / "thermal" / "series"
        original_path.rename(backup_dir)
        tmp_path.rename(original_path)
        shutil.rmtree(backup_dir)

    @staticmethod
    def _build_matrix_path(matrix_path: Path) -> Path:
        real_path = matrix_path / "series.txt"
        if not real_path.exists():
            (matrix_path / "series.txt.link").rename(real_path)
        return real_path

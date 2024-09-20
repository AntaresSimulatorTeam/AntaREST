# Copyright (c) 2024, RTE (https://www.rte-france.com)
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
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import dump_dataframe
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand, OutputTuple
from antarest.study.storage.variantstudy.model.model import CommandDTO

logger = logging.getLogger(__name__)


MODULATION_CAPACITY_COLUMN = 2
FO_RATE_COLUMN = 2
PO_RATE_COLUMN = 3


class GenerateThermalClusterTimeSeries(ICommand):
    """
    Command used to generate thermal cluster timeseries for an entire study
    """

    command_name: CommandName = CommandName.GENERATE_THERMAL_CLUSTER_TIMESERIES
    version: int = 1

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
        # 1- Get the seed and nb_years to generate
        # NB: Default seed in IHM Legacy: 5489, default seed in web: 3005489.
        general_data = study_data.tree.get(["settings", "generaldata"], depth=3)
        thermal_seed = general_data["seeds - Mersenne Twister"]["seed-tsgen-thermal"]
        nb_years = general_data["general"]["nbtimeseriesthermal"]
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
                url = ["input", "thermal", "prepro", area_id, thermal.id.lower(), "modulation"]
                matrix = study_data.tree.get_node(url)
                matrix_df = matrix.parse(return_dataframe=True)  # type: ignore
                modulation_capacity = matrix_df[MODULATION_CAPACITY_COLUMN].to_numpy()
                url = ["input", "thermal", "prepro", area_id, thermal.id.lower(), "data"]
                matrix = study_data.tree.get_node(url)
                matrix_df = matrix.parse(return_dataframe=True)  # type: ignore
                fo_duration, po_duration, fo_rate, po_rate, npo_min, npo_max = [
                    np.array(matrix_df[i], dtype=float if i in [FO_RATE_COLUMN, PO_RATE_COLUMN] else int)
                    for i in matrix_df.columns
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
                results = generator.generate_time_series(cluster, nb_years)
                generated_matrix = results.available_power
                # 8- Write the matrix inside the input folder.
                df = pd.DataFrame(data=generated_matrix, dtype=int)
                target_path = self._build_matrix_path(tmp_path / area_id / thermal.id.lower())
                dump_dataframe(df, target_path, None)

    def to_dto(self) -> CommandDTO:
        return CommandDTO(action=self.command_name.value, args={})

    def match_signature(self) -> str:
        return str(self.command_name.value)

    def match(self, other: "ICommand", equal: bool = False) -> bool:
        # Only used inside the cli app that no one uses I believe.
        if not isinstance(other, GenerateThermalClusterTimeSeries):
            return False
        return True

    def _create_diff(self, other: "ICommand") -> t.List["ICommand"]:
        # Only used inside the cli app that no one uses I believe.
        raise NotImplementedError()

    def get_inner_matrices(self) -> t.List[str]:
        # This is used to get used matrices and not remove them inside the garbage collector loop.
        return []

    @staticmethod
    def _replace_safely_original_files(study_path: Path, tmp_path: Path) -> None:
        original_path = study_path / "input" / "thermal" / "series"
        shutil.rmtree(original_path)
        tmp_path.rename(original_path)

    @staticmethod
    def _build_matrix_path(matrix_path: Path) -> Path:
        real_path = matrix_path / "series.txt"
        if not real_path.exists():
            (matrix_path / "series.txt.link").rename(real_path)
        return real_path

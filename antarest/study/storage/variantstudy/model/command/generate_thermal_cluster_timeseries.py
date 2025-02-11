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

import logging
import shutil
import tempfile
import typing as t
from pathlib import Path

import numpy as np
import pandas as pd
from antares.tsgen.duration_generator import ProbabilityLaw
from antares.tsgen.random_generator import MersenneTwisterRNG
from antares.tsgen.ts_generator import OutageGenerationParameters, ThermalCluster, TimeseriesGenerator
from typing_extensions import override

from antarest.study.storage.rawstudy.model.filesystem.config.model import Area, FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import LocalTSGenerationBehavior
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import dump_dataframe
from antarest.study.storage.utils import TS_GEN_PREFIX, TS_GEN_SUFFIX
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand, OutputTuple
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO

logger = logging.getLogger(__name__)


MODULATION_CAPACITY_COLUMN = 2


class GenerateThermalClusterTimeSeries(ICommand):
    """
    Command used to generate thermal cluster timeseries for an entire study
    """

    command_name: CommandName = CommandName.GENERATE_THERMAL_CLUSTER_TIMESERIES

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> OutputTuple:
        return CommandOutput(status=True, message="Nothing to do"), {}

    @override
    def _apply(self, study_data: FileStudy, listener: t.Optional[ICommandListener] = None) -> CommandOutput:
        study_path = study_data.config.study_path
        with tempfile.TemporaryDirectory(suffix=TS_GEN_SUFFIX, prefix=TS_GEN_PREFIX, dir=study_path.parent) as path:
            tmp_dir = Path(path)
            try:
                shutil.copytree(study_path / "input" / "thermal" / "series", tmp_dir, dirs_exist_ok=True)
                self._build_timeseries(study_data, tmp_dir, listener)
            except Exception as e:
                logger.error(f"Unhandled exception when trying to generate thermal timeseries: {e}", exc_info=True)
                raise
            else:
                self._replace_safely_original_files(study_path, tmp_dir)
                return CommandOutput(status=True, message="All time series were generated successfully")

    def _build_timeseries(
        self, study_data: FileStudy, tmp_path: Path, listener: t.Optional[ICommandListener] = None
    ) -> None:
        # 1- Get the seed and nb_years to generate
        # NB: Default seed in IHM Legacy: 5489, default seed in web: 3005489.
        general_data = study_data.tree.get(["settings", "generaldata"], depth=3)
        thermal_seed = general_data["seeds - Mersenne Twister"]["seed-tsgen-thermal"]
        nb_years = general_data["general"]["nbtimeseriesthermal"]
        # 2 - Build the generator
        rng = MersenneTwisterRNG(seed=thermal_seed)
        generator = TimeseriesGenerator(rng=rng, days=365)
        # 3- Do a first loop to know how many operations will be performed
        total_generations = sum(len(area.thermals) for area in study_data.config.areas.values())
        # 4- Loop through areas in alphabetical order
        areas: t.Dict[str, Area] = study_data.config.areas
        sorted_areas = {k: areas[k] for k in sorted(areas)}
        generation_performed = 0
        for area_id, area in sorted_areas.items():
            # 5- Loop through thermal clusters in alphabetical order
            sorted_thermals = sorted(area.thermals, key=lambda x: x.id)
            for thermal in sorted_thermals:
                try:
                    # 6 - Filters out clusters with no generation
                    if thermal.gen_ts == LocalTSGenerationBehavior.FORCE_NO_GENERATION:
                        generation_performed += 1
                        continue
                    # 7- Build the cluster
                    url = ["input", "thermal", "prepro", area_id, thermal.id.lower(), "modulation"]
                    matrix = study_data.tree.get_node(url)
                    assert isinstance(matrix, InputSeriesMatrix)
                    matrix_df = matrix.parse_as_dataframe()
                    modulation_capacity = matrix_df[MODULATION_CAPACITY_COLUMN].to_numpy()
                    url = ["input", "thermal", "prepro", area_id, thermal.id.lower(), "data"]
                    matrix = study_data.tree.get_node(url)
                    assert isinstance(matrix, InputSeriesMatrix)
                    matrix_df = matrix.parse_as_dataframe()
                    fo_duration = np.array(matrix_df[0], dtype=int)
                    po_duration = np.array(matrix_df[1], dtype=int)
                    fo_rate = np.array(matrix_df[2], dtype=float)
                    po_rate = np.array(matrix_df[3], dtype=float)
                    npo_min = np.array(matrix_df[4], dtype=int)
                    npo_max = np.array(matrix_df[5], dtype=int)
                    generation_params = OutageGenerationParameters(
                        unit_count=thermal.unit_count,
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
                    cluster = ThermalCluster(
                        outage_gen_params=generation_params,
                        nominal_power=thermal.nominal_capacity,
                        modulation=modulation_capacity,
                    )
                    # 8- Generate the time-series
                    results = generator.generate_time_series_for_clusters(cluster, nb_years)
                    generated_matrix = results.available_power
                    # 9- Write the matrix inside the input folder.
                    df = pd.DataFrame(data=generated_matrix)
                    df = df[list(df.columns)].astype(int)
                    target_path = self._build_matrix_path(tmp_path / area_id / thermal.id.lower())
                    dump_dataframe(df, target_path, None)
                    # 10- Notify the progress to the notifier
                    generation_performed += 1
                    if listener:
                        progress = int(100 * generation_performed / total_generations)
                        listener.notify_progress(progress)
                except Exception as e:
                    e.args = (f"Area {area_id}, cluster {thermal.id.lower()}: " + e.args[0],)
                    raise

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(action=self.command_name.value, args={}, study_version=self.study_version)

    @override
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

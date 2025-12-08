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
from typing import Optional

import numpy as np
import pandas as pd
from antares.tsgen.duration_generator import ProbabilityLaw
from antares.tsgen.random_generator import MersenneTwisterRNG
from antares.tsgen.ts_generator import OutageGenerationParameters, ThermalCluster, TimeseriesGenerator
from typing_extensions import override

from antarest.study.business.model.thermal_cluster_model import LocalTSGenerationBehavior
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    InnerMatrices,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
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
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        series_mapping: dict[str, dict[str, str]] = {}
        # 1- Get the seed and nb_years to generate
        # NB: Default seed in IHM Legacy: 5489, default seed in web: 3005489.
        nb_years = study_data.get_timeseries_config().thermal.number
        thermal_seed = study_data.get_advanced_parameters().seed_tsgen_thermal
        # 2 - Build the generator
        rng = MersenneTwisterRNG(seed=thermal_seed)
        generator = TimeseriesGenerator(rng=rng, days=365)
        # 3- Do a first loop to know how many operations will be performed
        all_thermals = study_data.get_all_thermals()
        total_generations = sum(len(values) for values in all_thermals.values())
        # 4- Loop through areas in alphabetical order
        sorted_areas = sorted(set(all_thermals))
        generation_performed = 0
        for area_id in sorted_areas:
            # 5- Loop through thermal clusters in alphabetical order
            sorted_thermal_ids = sorted(set(all_thermals[area_id]))
            for thermal_id in sorted_thermal_ids:
                thermal = all_thermals[area_id][thermal_id]

                try:
                    # 6 - Filters out clusters with no generation
                    if thermal.gen_ts == LocalTSGenerationBehavior.FORCE_NO_GENERATION:
                        generation_performed += 1
                        continue
                    # 7- Build the cluster
                    modulation_matrix = study_data.get_thermal_modulation(area_id, thermal_id)
                    modulation_capacity = modulation_matrix[MODULATION_CAPACITY_COLUMN].to_numpy()
                    prepro_matrix = study_data.get_thermal_prepro(area_id, thermal_id)
                    fo_duration = np.array(prepro_matrix[0], dtype=int)
                    po_duration = np.array(prepro_matrix[1], dtype=int)
                    fo_rate = np.array(prepro_matrix[2], dtype=float)
                    po_rate = np.array(prepro_matrix[3], dtype=float)
                    npo_min = np.array(prepro_matrix[4], dtype=int)
                    npo_max = np.array(prepro_matrix[5], dtype=int)
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
                    # 9- Write the matrix inside the matrix-store and store the id in memory
                    df = pd.DataFrame(data=generated_matrix)
                    df = df[list(df.columns)].astype(int)
                    matrix_id = self.command_context.matrix_service.create(df)
                    series_mapping.setdefault(area_id, {})[thermal_id] = matrix_id
                    # 10- Notify the progress to the notifier
                    generation_performed += 1
                    if listener:
                        progress = int(100 * generation_performed / total_generations)
                        listener.notify_progress(progress)

                except Exception as e:
                    return command_failed(f"Area {area_id}, cluster {thermal.id.lower()}: " + e.args[0])

        # 11- Once we've written all matrices inside the matrix-store, modify the input folder.
        for area_id, values in series_mapping.items():
            for thermal_id, series in values.items():
                study_data.save_thermal_series(area_id, thermal_id, series)

        return command_succeeded(message="All time series were generated successfully")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(action=self.command_name.value, args={}, study_version=self.study_version)

    @override
    def get_inner_matrices(self) -> InnerMatrices:
        return InnerMatrices(generates_matrices_at_run_time=True)

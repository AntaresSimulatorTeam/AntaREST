# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
from pathlib import Path
from unittest.mock import MagicMock, Mock

import numpy as np
import polars as pl
import pytest

from antarest.core.utils.polars import create_polars_dataframe
from antarest.study.business.model.area_model import AreaUIData
from antarest.study.business.model.area_properties_model import AreaProperties
from antarest.study.business.model.common import FilterOption
from antarest.study.business.model.config.advanced_parameters_model import (
    AdvancedParameters,
    InitialReservoirLevel,
    SimulationCore,
)
from antarest.study.business.model.config.general_model import BuildingMode, GeneralConfig
from antarest.study.business.model.config.optimization_config_model import (
    OptimizationPreferences,
)
from antarest.study.business.model.config.playlist_model import Playlist, PlaylistValues
from antarest.study.business.model.config.timeseries_config_model import TimeSeriesConfiguration, TimeSeriesType
from antarest.study.business.model.district_model import District, DistrictApplyFilter
from antarest.study.business.model.hydro_allocation_model import HydroAllocation, HydroAllocationArea
from antarest.study.business.model.hydro_model import HydroManagement, HydroProperties, InflowStructure
from antarest.study.business.model.link_model import Link
from antarest.study.business.model.scenario_builder_model import Ruleset
from antarest.study.business.model.sts_model import STStorage, STStorageAdditionalConstraint
from antarest.study.business.model.thematic_trimming_model import ThematicTrimming
from antarest.study.business.model.thermal_cluster_model import (
    ThermalCluster,
    ThermalClusterGroup,
)
from antarest.study.business.model.xpansion_model import (
    Master,
    Solver,
    UcType,
    XpansionResourceFileType,
    XpansionSensitivitySettings,
    XpansionSettings,
)
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.dao.study_conversion.study_converter import StudyConverter
from antarest.study.model import STUDY_VERSION_7_0, STUDY_VERSION_9_2
from antarest.study.service import StudyService
from antarest.study.storage.rawstudy.model.filesystem.config.model import Mode
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.helpers import with_admin_user
from tests.storage.integration.conftest import UUID


@with_admin_user
def test_nominal_case(storage_service, tmp_path: Path, command_context: CommandContext) -> None:
    """
    Ensures we can represent a study as a filesystem one.
    """
    source_path = tmp_path / "studies" / UUID
    new_path = tmp_path / "studies" / "new_study" / UUID
    storage_service.write_study_as_file_study(UUID, new_path, with_outputs=True)

    # Create DAO based on new study to test the study content.
    factory = storage_service.storage_service.raw_study_service.study_factory
    file_study = factory.create_from_fs(new_path, with_matrix_normalization=False, study_id="", use_cache=False)
    context = command_context
    file_study_dao = FileStudyTreeDao(
        file_study, False, context.generator_matrix_constants, context.blob_service, context.matrix_service, Mock()
    )

    # Version
    assert file_study_dao.get_version() == STUDY_VERSION_7_0

    # Links
    assert file_study_dao.get_links() == [
        Link(
            area1="de",
            area2="fr",
            hurdles_cost=True,
            filter_synthesis=[],
            filter_year_by_year=[FilterOption.HOURLY],
        ),
        Link(
            area1="es",
            area2="fr",
            hurdles_cost=True,
            filter_synthesis=[],
            filter_year_by_year=[FilterOption.HOURLY],
        ),
        Link(
            area1="fr",
            area2="it",
            hurdles_cost=True,
            filter_synthesis=[],
            filter_year_by_year=[FilterOption.HOURLY],
        ),
    ]
    series = file_study_dao.get_link_series("fr", "it")
    expected_series = create_polars_dataframe(np.zeros((8760, 8)))
    expected_series = expected_series.with_columns(
        [pl.lit(100000).alias("0"), pl.lit(100000).alias("1"), pl.lit(0.01).alias("2"), pl.lit(0.01).alias("3")]
    )
    pl.testing.assert_frame_equal(series, expected_series, check_dtypes=False)

    # Binding constraints
    assert file_study_dao.get_all_constraints() == {}

    # Settings
    assert file_study_dao.get_general_config() == GeneralConfig(
        mode=Mode.ADEQUACY,
        first_day=1,
        last_day=7,
        leap_year=False,
        horizon="2030",
        building_mode=BuildingMode.CUSTOM,
        selection_mode=True,
        mc_scenario=True,
        filtering=True,
    )
    assert file_study_dao.get_optimization_preferences() == OptimizationPreferences()
    assert file_study_dao.get_advanced_parameters() == AdvancedParameters(
        initial_reservoir_levels=InitialReservoirLevel.COLD_START, number_of_cores_mode=SimulationCore.MAXIMUM
    )
    assert file_study_dao.get_playlist_config() == Playlist(years={1: PlaylistValues(status=True, weight=1)})
    assert file_study_dao.get_timeseries_config() == TimeSeriesConfiguration(thermal=TimeSeriesType(number=1))
    assert file_study_dao.get_thematic_trimming() == ThematicTrimming(
        solar=True, nuclear=True, lignite=True, coal=True, gas=True, oil=True, mix_fuel=True, misc_dtg=True
    )

    # Scenario builder
    assert file_study_dao.get_ruleset() == Ruleset(
        load={"de": {"0": 1}, "es": {"0": 1}, "fr": {"0": 1}, "it": {"0": 1}},
        thermal={
            "de": {
                "01_solar": {"0": 1},
                "02_wind_on": {"0": 1},
                "03_wind_off": {"0": 1},
                "04_res": {"0": 1},
                "05_nuclear": {"0": 1},
                "06_coal": {"0": 1},
                "07_gas": {"0": 1},
                "08_non-res": {"0": 1},
                "09_hydro_pump": {"0": 1},
            },
            "es": {
                "01_solar": {"0": 1},
                "02_wind_on": {"0": 1},
                "03_wind_off": {"0": 1},
                "04_res": {"0": 1},
                "05_nuclear": {"0": 1},
                "06_coal": {"0": 1},
                "07_gas": {"0": 1},
                "08_non-res": {"0": 1},
                "09_hydro_pump": {"0": 1},
            },
            "fr": {
                "01_solar": {"0": 1},
                "02_wind_on": {"0": 1},
                "03_wind_off": {"0": 1},
                "04_res": {"0": 1},
                "05_nuclear": {"0": 1},
                "06_coal": {"0": 1},
                "07_gas": {"0": 1},
                "08_non-res": {"0": 1},
                "09_hydro_pump": {"0": 1},
            },
            "it": {
                "01_solar": {"0": 1},
                "02_wind_on": {"0": 1},
                "03_wind_off": {"0": 1},
                "04_res": {"0": 1},
                "05_nuclear": {"0": 1},
                "06_coal": {"0": 1},
                "07_gas": {"0": 1},
                "08_non-res": {"0": 1},
                "09_hydro_pump": {"0": 1},
            },
        },
        hydro={"de": {"0": 1}, "es": {"0": 1}, "fr": {"0": 1}, "it": {"0": 1}},
        wind={"de": {"0": 1}, "es": {"0": 1}, "fr": {"0": 1}, "it": {"0": 1}},
        solar={"de": {"0": 1}, "es": {"0": 1}, "fr": {"0": 1}, "it": {"0": 1}},
    )

    # Area properties
    assert file_study_dao.get_all_area_properties() == {
        "de": AreaProperties(
            energy_cost_unsupplied=3000.0,
            filter_synthesis={"monthly", "daily"},
            filter_by_year={"hourly", "annual", "weekly"},
        ),
        "es": AreaProperties(
            energy_cost_unsupplied=3000.0,
            filter_synthesis={"monthly", "daily"},
            filter_by_year={"hourly", "annual", "weekly"},
        ),
        "fr": AreaProperties(
            energy_cost_unsupplied=3000.0,
            filter_synthesis=set(),
            filter_by_year={"hourly"},
        ),
        "it": AreaProperties(
            energy_cost_unsupplied=3000.0,
            filter_synthesis=set(),
            filter_by_year={"hourly"},
        ),
    }

    # Area ui
    assert file_study_dao.get_all_areas_ui_info() == {
        "de": AreaUIData(
            ui={"x": 1, "y": 135, "color_r": 0, "color_g": 128, "color_b": 255, "layers": "0"},
            layer_x={"0": 1},
            layer_y={"0": 135},
            layer_color={"0": "0, 128, 255"},
        ),
        "es": AreaUIData(
            ui={"x": -369, "y": -74, "color_r": 0, "color_g": 128, "color_b": 255, "layers": "0"},
            layer_x={"0": -369},
            layer_y={"0": -74},
            layer_color={"0": "0, 128, 255"},
        ),
        "fr": AreaUIData(
            ui={"x": -309, "y": -1, "color_r": 0, "color_g": 128, "color_b": 255, "layers": "0"},
            layer_x={"0": -309},
            layer_y={"0": -1},
            layer_color={"0": "0, 128, 255"},
        ),
        "it": AreaUIData(
            ui={"x": -99, "y": -55, "color_r": 0, "color_g": 128, "color_b": 255, "layers": "0"},
            layer_x={"0": -99},
            layer_y={"0": -55},
            layer_color={"0": "0, 128, 255"},
        ),
    }

    # Districts
    assert file_study_dao.get_districts() == [
        District(
            id="all areas",
            output=False,
            comments="Spatial aggregates on all areas",
            name="All areas",
            apply_filter=DistrictApplyFilter.add_all,
        )
    ]

    # Load
    load = file_study_dao.get_load("fr")
    expected_load = create_polars_dataframe(np.array(53 * list(range(0, 168 * 100, 100)))[:8760])
    pl.testing.assert_frame_equal(load, expected_load, check_dtypes=False)

    # Thermal series
    thermal_series = file_study_dao.get_thermal_series("fr", "01_solar")
    assert thermal_series.equals(create_polars_dataframe(8760 * [2000]))

    # Thermal clusters
    expected_clusters = {
        "01_solar": ThermalCluster(
            name="01_solar",
            nominal_capacity=1000000.0,
            group=ThermalClusterGroup.OTHER1,
            marginal_cost=10.0,
            market_bid_cost=10.0,
        ),
        "02_wind_on": ThermalCluster(
            name="02_wind_on",
            nominal_capacity=1000000.0,
            group=ThermalClusterGroup.OTHER1,
            marginal_cost=20.0,
            market_bid_cost=20.0,
        ),
        "03_wind_off": ThermalCluster(
            name="03_wind_off",
            nominal_capacity=1000000.0,
            group=ThermalClusterGroup.OTHER1,
            marginal_cost=30.0,
            market_bid_cost=30.0,
        ),
        "04_res": ThermalCluster(
            name="04_res",
            nominal_capacity=1000000.0,
            group=ThermalClusterGroup.OTHER1,
            marginal_cost=40.0,
            market_bid_cost=40.0,
        ),
        "05_nuclear": ThermalCluster(
            name="05_nuclear",
            nominal_capacity=1000000.0,
            group=ThermalClusterGroup.OTHER1,
            marginal_cost=50.0,
            market_bid_cost=50.0,
        ),
        "06_coal": ThermalCluster(
            name="06_coal",
            nominal_capacity=1000000.0,
            group=ThermalClusterGroup.OTHER1,
            marginal_cost=60.0,
            market_bid_cost=60.0,
        ),
        "07_gas": ThermalCluster(
            name="07_gas",
            nominal_capacity=1000000.0,
            group=ThermalClusterGroup.OTHER1,
            marginal_cost=70.0,
            market_bid_cost=70.0,
        ),
        "08_non-res": ThermalCluster(
            name="08_non-res",
            nominal_capacity=1000000.0,
            group=ThermalClusterGroup.OTHER1,
            marginal_cost=80.0,
            market_bid_cost=80.0,
        ),
        "09_hydro_pump": ThermalCluster(
            name="09_hydro_pump",
            nominal_capacity=1000000.0,
            group=ThermalClusterGroup.OTHER1,
            marginal_cost=90.0,
            market_bid_cost=90.0,
        ),
    }
    assert file_study_dao.get_all_thermals() == {
        "de": expected_clusters,
        "es": expected_clusters,
        "fr": expected_clusters,
        "it": expected_clusters,
    }

    # Hydro
    expected_properties = HydroProperties(
        management_options=HydroManagement(intra_daily_modulation=2.0), inflow_structure=InflowStructure()
    )
    assert file_study_dao.get_all_hydro_properties() == {
        "de": expected_properties,
        "es": expected_properties,
        "fr": expected_properties,
        "it": expected_properties,
    }
    correlation_matrix = file_study_dao.get_hydro_correlation_matrix()
    assert correlation_matrix.index == correlation_matrix.columns == ["de", "es", "fr", "it"]
    assert correlation_matrix.data.tolist() == [
        [1.0, 0.0, 0.25, 0.0],
        [0.0, 1.0, 0.75, 0.12],
        [0.25, 0.75, 1.0, 0.75],
        [0.0, 0.12, 0.75, 1.0],
    ]

    for area_id in ["de", "es", "fr", "it"]:
        assert file_study_dao.get_hydro_allocation(area_id) == HydroAllocation(
            allocation=[HydroAllocationArea(area_id=area_id, coefficient=1)]
        )

    # User folder
    assert list(file_study_dao.get_all_user_resources()) == []

    # Xpansion
    assert file_study_dao.get_xpansion_settings() == XpansionSettings(
        master=Master.RELAXED,
        uc_type=UcType.EXPANSION_FAST,
        optimality_gap=1000000.0,
        relative_gap=1e-06,
        relaxed_optimality_gap=1e-05,
        max_iteration=200,
        solver=Solver.XPRESS,
        log_level=1,
        separation_parameter=0.5,
        batch_size=96,
        yearly_weights="",
        additional_constraints="",
        timelimit=10000,
        sensitivity_config=XpansionSensitivitySettings(epsilon=0.0, projection=[], capex=False),
    )

    assert file_study_dao.get_all_xpansion_candidates() == []
    assert file_study_dao.get_xpansion_resources(XpansionResourceFileType.CONSTRAINTS) == []
    assert file_study_dao.get_xpansion_resources(XpansionResourceFileType.WEIGHTS) == []
    assert file_study_dao.get_xpansion_resources(XpansionResourceFileType.CAPACITIES) == []

    # Outputs
    outputs_before = [f.name for f in (source_path / "output").iterdir()]
    assert [f.name for f in (new_path / "output").iterdir()] == outputs_before

    # Ensures the matrices are not normalized
    assert (new_path / "input" / "load" / "series" / "load_de.txt").exists()
    assert not (new_path / "input" / "load" / "series" / "load_de.txt.link").exists()


@with_admin_user
def test_no_outputs(storage_service: StudyService, tmp_path: Path) -> None:
    """
    Ensures the outputs aren't copied when didn't asked to
    """
    new_path = tmp_path / "studies" / "new_study" / UUID
    storage_service.write_study_as_file_study(UUID, new_path, with_outputs=False)
    assert not list((new_path / "output").iterdir())


@with_admin_user
def test_matrices_normalized(storage_service: StudyService, tmp_path: Path) -> None:
    """
    Ensures the matrices are normalized when asked to.
    """
    new_path = tmp_path / "studies" / "new_study" / UUID
    storage_service.write_study_as_file_study(UUID, new_path, with_outputs=False, normalize_matrices=True)
    assert not (new_path / "input" / "load" / "series" / "load_de.txt").exists()
    assert (new_path / "input" / "load" / "series" / "load_de.txt.link").exists()


def test_convert_short_term_storages_also_converts_additional_constraint_matrix() -> None:
    source_dao = MagicMock()
    new_dao = MagicMock()
    source_dao.get_version.return_value = STUDY_VERSION_9_2
    new_dao.get_version.return_value = STUDY_VERSION_9_2

    converter = StudyConverter(source_dao=source_dao, new_dao=new_dao, matrix_service=MagicMock())

    storage = STStorage(id="battery", name="Battery")
    constraint = STStorageAdditionalConstraint(id="c1", name="Constraint 1")

    converter._convert_short_term_storages(
        storages={"fr": {"battery": storage}}, constraints={"fr": {"battery": [constraint]}}
    )

    source_dao.get_all_st_storage_additional_constraint_matrices.assert_called_once()
    new_dao.save_st_storage_constraint_matrices.assert_called_once()


def test_conversion_with_different_versions() -> None:
    source_dao = MagicMock()
    new_dao = MagicMock()
    source_dao.get_version.return_value = STUDY_VERSION_9_2
    new_dao.get_version.return_value = STUDY_VERSION_7_0

    with pytest.raises(ValueError):
        StudyConverter(source_dao=source_dao, new_dao=new_dao, matrix_service=MagicMock())

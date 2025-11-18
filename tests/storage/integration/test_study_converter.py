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
from pathlib import Path

from antarest.study.business.model.common import FilterOption
from antarest.study.business.model.hydro_allocation_model import HydroAllocation, HydroAllocationArea
from antarest.study.business.model.hydro_model import HydroManagement, HydroProperties, InflowStructure
from antarest.study.business.model.link_model import AssetType, Link, LinkStyle, TransmissionCapacity
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
from antarest.study.model import STUDY_VERSION_7_0
from antarest.study.service import StudyService
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.helpers import with_admin_user
from tests.storage.integration.conftest import UUID


@with_admin_user
def test_convert_study(storage_service: StudyService, tmp_path: Path, command_context: CommandContext) -> None:
    """
    For the moment, it only ensures the method doesn't crash
    """
    source_path = tmp_path / "studies" / UUID
    new_path = tmp_path / "studies" / "new_study" / UUID
    storage_service.write_study_as_file_study(UUID, new_path)

    # Create DAO based on new study to test the study content.
    factory = storage_service.storage_service.raw_study_service.study_factory
    file_study = factory.create_from_fs(new_path, with_matrix_normalization=False, study_id="", use_cache=False)
    context = command_context
    file_study_dao = FileStudyTreeDao(file_study, context.generator_matrix_constants, context.blob_service)

    # Version
    assert file_study_dao.get_version() == STUDY_VERSION_7_0

    # Links
    assert file_study_dao.get_links() == [
        Link(
            area1="de",
            area2="fr",
            hurdles_cost=True,
            loop_flow=False,
            use_phase_shifter=False,
            transmission_capacities=TransmissionCapacity.ENABLED,
            asset_type=AssetType.AC,
            display_comments=True,
            comments="",
            colorr=112,
            colorb=112,
            colorg=112,
            link_width=1.0,
            link_style=LinkStyle.PLAIN,
            filter_synthesis=[],
            filter_year_by_year=[FilterOption.HOURLY],
        ),
        Link(
            area1="es",
            area2="fr",
            hurdles_cost=True,
            loop_flow=False,
            use_phase_shifter=False,
            transmission_capacities=TransmissionCapacity.ENABLED,
            asset_type=AssetType.AC,
            display_comments=True,
            comments="",
            colorr=112,
            colorb=112,
            colorg=112,
            link_width=1.0,
            link_style=LinkStyle.PLAIN,
            filter_synthesis=[],
            filter_year_by_year=[FilterOption.HOURLY],
        ),
        Link(
            area1="fr",
            area2="it",
            hurdles_cost=True,
            loop_flow=False,
            use_phase_shifter=False,
            transmission_capacities=TransmissionCapacity.ENABLED,
            asset_type=AssetType.AC,
            display_comments=True,
            comments="",
            colorr=112,
            colorb=112,
            colorg=112,
            link_width=1.0,
            link_style=LinkStyle.PLAIN,
            filter_synthesis=[],
            filter_year_by_year=[FilterOption.HOURLY],
        ),
    ]

    # Binding constraints
    assert file_study_dao.get_all_constraints() == {}

    # Settings

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
        management_options=HydroManagement(
            inter_daily_breakdown=1.0,
            intra_daily_modulation=2.0,
            inter_monthly_breakdown=1.0,
            reservoir=False,
            reservoir_capacity=0.0,
            follow_load=True,
            use_water=False,
            hard_bounds=False,
            initialize_reservoir_date=0,
            use_heuristic=True,
            power_to_level=False,
            use_leeway=False,
            leeway_low=1.0,
            leeway_up=1.0,
            pumping_efficiency=1.0,
            overflow_spilled_cost_difference=None,
        ),
        inflow_structure=InflowStructure(inter_monthly_correlation=0.5),
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

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
from unittest.mock import Mock

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.area_management import AreaManager
from antarest.study.business.link_management import LinkManager
from antarest.study.business.model.area_model import AreaCreation, AreaUIUpdate
from antarest.study.business.model.district_model import District
from antarest.study.business.model.link_model import AssetType, Link, TransmissionCapacity
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.business.study_interface import StudyInterface
from antarest.study.model import STUDY_VERSION_7_0
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    AreaConfig,
    FileStudyTreeConfig,
    LinkConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.variantstudy.model.command.common import FilteringOptions
from tests.helpers import file_study_interface


def test_area_crud(
    study: StudyInterface, matrix_service: ISimpleMatrixService, area_manager: AreaManager, link_manager: LinkManager
) -> None:
    file_study = study.get_files()
    assert len(file_study.config.areas.keys()) == 0

    area_manager.create_area(study, AreaCreation(name="test"))
    assert len(file_study.config.areas.keys()) == 1

    area_manager.update_area_ui(study, "test", AreaUIUpdate(x=100, y=200, color_rgb=(255, 0, 100)), layer="0")
    assert file_study.tree.get(["input", "areas", "test", "ui", "ui"]) == {
        "x": 100,
        "y": 200,
        "color_r": 255,
        "color_g": 0,
        "color_b": 100,
        "layers": 0,
    }

    area_manager.create_area(study, AreaCreation(name="test2"))

    link_manager.create_link(
        study,
        Link(
            area1="test",
            area2="test2",
        ),
    )
    assert file_study.config.areas["test"].links.get("test2") is not None

    link_manager.delete_link(study, "test", "test2")
    assert file_study.config.areas["test"].links.get("test2") is None
    area_manager.delete_area(study, "test")
    area_manager.delete_area(study, "test2")
    assert len(file_study.config.areas.keys()) == 0


def test_get_all_area(area_manager: AreaManager, link_manager: LinkManager) -> None:
    config = FileStudyTreeConfig(
        study_path=Path("somepath"),
        path=Path("somepath"),
        study_id="",
        version=STUDY_VERSION_7_0,
        areas={
            "a1": AreaConfig(
                name="a1",
                links={
                    "a2": LinkConfig(filters_synthesis=[], filters_year=[]),
                    "a3": LinkConfig(filters_synthesis=[], filters_year=[]),
                },
                thermals=[ThermalCluster(name="a", enabled=True)],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            ),
            "a2": AreaConfig(
                name="a2",
                links={"a3": LinkConfig(filters_synthesis=[], filters_year=[])},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            ),
            "a3": AreaConfig(
                name="a3",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            ),
        },
        districts={"s1": District(id="s1", name="s1", add_areas=["a1"])},
    )
    file_tree_mock = Mock(spec=FileStudyTree, matrix_storage_context=Mock(), config=config)

    study_interface = file_study_interface(FileStudy(config, file_tree_mock))
    file_tree_mock.get.side_effect = [
        {
            "a": {
                "name": "A",
                "unitcount": 1,
                "nominalcapacity": 500,
                "min-stable-power": 200,
            }
        },
        {},
        {},
    ]

    expected_areas = [
        {
            "name": "a1",
            "thermals": [
                {
                    "co2": 0.0,
                    "cost_generation": None,
                    "efficiency": None,
                    "enabled": True,
                    "fixed_cost": 0.0,
                    "gen_ts": "use global",
                    "group": "other 1",
                    "id": "A",
                    "law_forced": "uniform",
                    "law_planned": "uniform",
                    "marginal_cost": 0.0,
                    "market_bid_cost": 0.0,
                    "min_down_time": 1,
                    "min_stable_power": 200.0,
                    "min_up_time": 1,
                    "must_run": False,
                    "name": "A",
                    "nh3": None,
                    "nmvoc": None,
                    "nominal_capacity": 500.0,
                    "nox": None,
                    "op1": None,
                    "op2": None,
                    "op3": None,
                    "op4": None,
                    "op5": None,
                    "pm10": None,
                    "pm2_5": None,
                    "pm5": None,
                    "so2": None,
                    "spinning": 0.0,
                    "spread_cost": 0.0,
                    "startup_cost": 0.0,
                    "unit_count": 1,
                    "variable_o_m_cost": None,
                    "volatility_forced": 0.0,
                    "volatility_planned": 0.0,
                }
            ],
            "id": "a1",
        },
        {
            "name": "a2",
            "thermals": [],
            "id": "a2",
        },
        {
            "name": "a3",
            "thermals": [],
            "id": "a3",
        },
    ]
    areas = area_manager.get_all_areas_info(study_interface)
    assert [area.model_dump() for area in areas] == expected_areas

    # `AreaType.DISTRICT` is now ignored but kept for backward compatibility.
    file_tree_mock.get.side_effect = [
        {
            "a": {
                "name": "A",
                "unitcount": 1,
                "nominalcapacity": 500,
                "min-stable-power": 200,
            }
        },
        {},
        {},
    ]

    file_tree_mock.get.side_effect = [{}, {}, {}]
    expected_all = [
        {
            "name": "a1",
            "thermals": [],
            "id": "a1",
        },
        {
            "name": "a2",
            "thermals": [],
            "id": "a2",
        },
        {
            "name": "a3",
            "thermals": [],
            "id": "a3",
        },
    ]
    all_areas = area_manager.get_all_areas_info(study_interface)
    assert expected_all == [area.model_dump() for area in all_areas]

    file_tree_mock.get.side_effect = [
        {
            "a2": {
                "hurdles-cost": False,
                "loop-flow": False,
                "use-phase-shifter": False,
                "transmission-capacities": TransmissionCapacity.ENABLED,
                "asset-type": AssetType.AC,
                "display-comments": False,
                "filter-synthesis": FilteringOptions.FILTER_SYNTHESIS,
                "filter-year-by-year": FilteringOptions.FILTER_YEAR_BY_YEAR,
            },
            "a3": {
                "hurdles-cost": False,
                "loop-flow": False,
                "use-phase-shifter": False,
                "transmission-capacities": TransmissionCapacity.ENABLED,
                "asset-type": AssetType.AC,
                "display-comments": False,
                "filter-synthesis": FilteringOptions.FILTER_SYNTHESIS,
                "filter-year-by-year": FilteringOptions.FILTER_YEAR_BY_YEAR,
            },
        },
        {
            "a3": {
                "hurdles-cost": False,
                "loop-flow": False,
                "use-phase-shifter": False,
                "transmission-capacities": TransmissionCapacity.ENABLED,
                "asset-type": AssetType.AC,
                "display-comments": False,
                "filter-synthesis": FilteringOptions.FILTER_SYNTHESIS,
                "filter-year-by-year": FilteringOptions.FILTER_YEAR_BY_YEAR,
            }
        },
        {},
    ]
    links = link_manager.get_all_links(study_interface)
    assert [
        {
            "area1": "a1",
            "area2": "a2",
            "asset_type": "ac",
            "colorb": 112,
            "colorg": 112,
            "colorr": 112,
            "display_comments": False,
            "comments": "",
            "filter_synthesis": "hourly, daily, weekly, monthly, annual",
            "filter_year_by_year": "hourly, daily, weekly, monthly, annual",
            "hurdles_cost": False,
            "link_style": "plain",
            "link_width": 1.0,
            "loop_flow": False,
            "transmission_capacities": "enabled",
            "use_phase_shifter": False,
        },
        {
            "area1": "a1",
            "area2": "a3",
            "asset_type": "ac",
            "colorb": 112,
            "colorg": 112,
            "colorr": 112,
            "display_comments": False,
            "comments": "",
            "filter_synthesis": "hourly, daily, weekly, monthly, annual",
            "filter_year_by_year": "hourly, daily, weekly, monthly, annual",
            "hurdles_cost": False,
            "link_style": "plain",
            "link_width": 1.0,
            "loop_flow": False,
            "transmission_capacities": "enabled",
            "use_phase_shifter": False,
        },
        {
            "area1": "a2",
            "area2": "a3",
            "asset_type": "ac",
            "colorb": 112,
            "colorg": 112,
            "colorr": 112,
            "display_comments": False,
            "comments": "",
            "filter_synthesis": "hourly, daily, weekly, monthly, annual",
            "filter_year_by_year": "hourly, daily, weekly, monthly, annual",
            "hurdles_cost": False,
            "link_style": "plain",
            "link_width": 1.0,
            "loop_flow": False,
            "transmission_capacities": "enabled",
            "use_phase_shifter": False,
        },
    ] == [link.model_dump(mode="json") for link in links]

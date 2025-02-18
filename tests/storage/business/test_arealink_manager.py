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

import json
from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

import pytest

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.matrixstore.uri_resolver_service import UriResolverService
from antarest.study.business.area_management import AreaCreationDTO, AreaManager, AreaType, UpdateAreaUi
from antarest.study.business.link_management import LinkDTO, LinkManager
from antarest.study.business.model.link_model import AssetType, TransmissionCapacity
from antarest.study.business.study_interface import FileStudyInterface, StudyInterface
from antarest.study.model import Patch, PatchArea, PatchCluster
from antarest.study.storage.rawstudy.model.filesystem.config.files import build
from antarest.study.storage.rawstudy.model.filesystem.config.model import Area, DistrictSet, FileStudyTreeConfig, Link
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import ThermalConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.variantstudy.model.command.common import FilteringOptions
from tests.storage.business.assets import ASSETS_DIR


@pytest.fixture
def study(empty_study: FileStudy) -> StudyInterface:
    return FileStudyInterface(empty_study)


@pytest.fixture(name="empty_study")
def empty_study_fixture(tmp_path: Path, matrix_service: ISimpleMatrixService) -> FileStudy:
    """
    Fixture for preparing an empty study in the `tmp_path`
    based on the "empty_study_810.zip" asset.

    Args:
        tmp_path: The temporary path provided by pytest.

    Returns:
        An instance of the `FileStudy` class representing the empty study.
    """
    study_id = "5c22caca-b100-47e7-bbea-8b1b97aa26d9"
    study_path = tmp_path.joinpath(study_id)
    study_path.mkdir()
    with ZipFile(ASSETS_DIR / "empty_study_810.zip") as zip_output:
        zip_output.extractall(path=study_path)
    config = build(study_path, study_id)
    context = ContextServer(matrix_service, UriResolverService(matrix_service))
    return FileStudy(config, FileStudyTree(context, config))


def test_area_crud(
    study: StudyInterface, matrix_service: ISimpleMatrixService, area_manager: AreaManager, link_manager: LinkManager
) -> None:
    file_study = study.get_files()
    assert len(file_study.config.areas.keys()) == 0

    area_manager.create_area(study, AreaCreationDTO(name="test", type=AreaType.AREA))
    assert len(file_study.config.areas.keys()) == 1
    assert json.loads((file_study.config.study_path / "patch.json").read_text())["areas"]["test"]["country"] is None

    area_manager.update_area_ui(study, "test", UpdateAreaUi(x=100, y=200, color_rgb=(255, 0, 100)), layer="0")
    assert file_study.tree.get(["input", "areas", "test", "ui", "ui"]) == {
        "x": 100,
        "y": 200,
        "color_r": 255,
        "color_g": 0,
        "color_b": 100,
        "layers": 0,
    }

    area_manager.create_area(study, AreaCreationDTO(name="test2", type=AreaType.AREA))

    link_manager.create_link(
        study,
        LinkDTO(
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
        version=-1,
        areas={
            "a1": Area(
                name="a1",
                links={
                    "a2": Link(filters_synthesis=[], filters_year=[]),
                    "a3": Link(filters_synthesis=[], filters_year=[]),
                },
                thermals=[ThermalConfig(id="a", name="a", enabled=True)],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            ),
            "a2": Area(
                name="a2",
                links={"a3": Link(filters_synthesis=[], filters_year=[])},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            ),
            "a3": Area(
                name="a3",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            ),
        },
        sets={"s1": DistrictSet(areas=["a1"])},
    )
    file_tree_mock = Mock(spec=FileStudyTree, context=Mock(), config=config)

    study_interface = Mock(spec=StudyInterface)
    study_interface.get_files.return_value = FileStudy(config, file_tree_mock)
    study_interface.get_patch_data.return_value = Patch(
        areas={"a1": PatchArea(country="fr")},
        thermal_clusters={"a1.a": PatchCluster.model_validate({"code-oi": "1"})},
    )
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
            "type": AreaType.AREA,
            "metadata": {"country": "fr", "tags": []},
            "set": None,
            "thermals": [
                {
                    "id": "a",
                    "name": "A",
                    "enabled": True,
                    "unitcount": 1,
                    "nominalcapacity": 500,
                    "group": None,
                    "min_stable_power": 200,
                    "min_up_time": None,
                    "min_down_time": None,
                    "spinning": None,
                    "marginal_cost": None,
                    "spread_cost": None,
                    "market_bid_cost": None,
                    "type": None,
                    "code_oi": "1",
                }
            ],
            "id": "a1",
        },
        {
            "name": "a2",
            "type": AreaType.AREA,
            "metadata": {"country": None, "tags": []},
            "set": None,
            "thermals": [],
            "id": "a2",
        },
        {
            "name": "a3",
            "type": AreaType.AREA,
            "metadata": {"country": None, "tags": []},
            "set": None,
            "thermals": [],
            "id": "a3",
        },
    ]
    areas = area_manager.get_all_areas(study_interface, AreaType.AREA)
    assert expected_areas == [area.model_dump() for area in areas]

    expected_clusters = [
        {
            "name": "s1",
            "type": AreaType.DISTRICT,
            "metadata": {"country": None, "tags": []},
            "set": ["a1"],
            "thermals": None,
            "id": "s1",
        }
    ]
    clusters = area_manager.get_all_areas(study_interface, AreaType.DISTRICT)
    assert expected_clusters == [area.model_dump() for area in clusters]

    file_tree_mock.get.side_effect = [{}, {}, {}]
    expected_all = [
        {
            "name": "a1",
            "type": AreaType.AREA,
            "metadata": {"country": "fr", "tags": []},
            "set": None,
            "thermals": [],
            "id": "a1",
        },
        {
            "name": "a2",
            "type": AreaType.AREA,
            "metadata": {"country": None, "tags": []},
            "set": None,
            "thermals": [],
            "id": "a2",
        },
        {
            "name": "a3",
            "type": AreaType.AREA,
            "metadata": {"country": None, "tags": []},
            "set": None,
            "thermals": [],
            "id": "a3",
        },
        {
            "name": "s1",
            "type": AreaType.DISTRICT,
            "metadata": {"country": None, "tags": []},
            "set": ["a1"],
            "thermals": None,
            "id": "s1",
        },
    ]
    all_areas = area_manager.get_all_areas(study_interface)
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


def test_update_area(area_manager: AreaManager):

    config = FileStudyTreeConfig(
        study_path=Path("somepath"),
        path=Path("somepath"),
        study_id="",
        version=-1,
        areas={
            "a1": Area(
                name="a1",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            ),
            "a2": Area(
                name="a2",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            ),
        },
        sets={"s1": DistrictSet(areas=["a1"])},
    )
    study_interface = Mock(spec=StudyInterface)

    study_interface.get_files.return_value = FileStudy(config=config, tree=FileStudyTree(context=Mock(), config=config))
    study_interface.get_patch_data.return_value = Patch(areas={"a1": PatchArea(country="fr")})

    new_area_info = area_manager.update_area_metadata(study_interface, "a1", PatchArea(country="fr"))
    assert new_area_info.id == "a1"
    assert new_area_info.metadata.model_dump() == {"country": "fr", "tags": []}


def test_update_clusters(area_manager: AreaManager):

    config = FileStudyTreeConfig(
        study_path=Path("somepath"),
        path=Path("somepath"),
        study_id="",
        version=-1,
        areas={
            "a1": Area(
                name="a1",
                links={},
                thermals=[ThermalConfig(id="a", name="a", enabled=True)],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            )
        },
    )
    file_tree_mock = Mock(spec=FileStudyTree, context=Mock(), config=config)
    study_interface = Mock(spec=StudyInterface)

    study_interface.get_files.return_value = FileStudy(config=config, tree=file_tree_mock)
    study_interface.get_patch_data.return_value = Patch(
        areas={"a1": PatchArea(country="fr")},
        thermal_clusters={"a1.a": PatchCluster.model_validate({"code-oi": "1"})},
    )
    file_tree_mock.get.side_effect = [
        {
            "a": {
                "name": "A",
                "unitcount": 1,
                "nominalcapacity": 500,
                "min-stable-power": 200,
            }
        }
    ]

    new_area_info = area_manager.update_thermal_cluster_metadata(study_interface, "a1", {"a": PatchCluster(type="a")})
    assert len(new_area_info.thermals) == 1
    assert new_area_info.thermals[0].type == "a"
    assert new_area_info.thermals[0].code_oi is None

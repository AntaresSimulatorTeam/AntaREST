from pathlib import Path
from unittest.mock import Mock

from antarest.study.business.link_management import LinkManager
from antarest.study.model import RawStudy, Patch, PatchArea, PatchCluster
from antarest.study.business.area_management import (
    AreaManager,
    AreaType,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
    Area,
    Set,
    Link,
    Cluster,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)
from antarest.study.storage.rawstudy.raw_study_service import (
    RawStudyService,
)
from antarest.study.storage.storage_service import StudyStorageService


def test_create_area():
    raw_study_service = Mock(spec=RawStudyService)
    area_manager = AreaManager(
        storage_service=StudyStorageService(raw_study_service, Mock())
    )
    pass


def test_get_all_area():
    raw_study_service = Mock(spec=RawStudyService)
    area_manager = AreaManager(
        storage_service=StudyStorageService(raw_study_service, Mock())
    )
    link_manager = LinkManager(
        storage_service=StudyStorageService(raw_study_service, Mock())
    )

    study = RawStudy()
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
                thermals=[Cluster(id="a", name="a", enabled=True)],
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
        sets={"s1": Set(areas=["a1"])},
    )
    file_tree_mock = Mock(spec=FileStudyTree, context=Mock(), config=config)
    raw_study_service.get_raw.return_value = FileStudy(
        config=config, tree=file_tree_mock
    )

    area_manager.patch_service = Mock()
    area_manager.patch_service.get.return_value = Patch(
        areas={"a1": PatchArea(country="fr")},
        thermal_clusters={"a1.a": PatchCluster.parse_obj({"code-oi": "1"})},
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
            "metadata": {"country": "fr"},
            "set": None,
            "thermals": [
                {
                    "id": "a",
                    "name": "A",
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
            "metadata": {"country": None},
            "set": None,
            "thermals": [],
            "id": "a2",
        },
        {
            "name": "a3",
            "type": AreaType.AREA,
            "metadata": {"country": None},
            "set": None,
            "thermals": [],
            "id": "a3",
        },
    ]
    areas = area_manager.get_all_areas(study, AreaType.AREA)
    assert expected_areas == [area.dict() for area in areas]

    expected_clusters = [
        {
            "name": "s1",
            "type": AreaType.DISTRICT,
            "metadata": {"country": None},
            "set": ["a1"],
            "thermals": None,
            "id": "s1",
        }
    ]
    clusters = area_manager.get_all_areas(study, AreaType.DISTRICT)
    assert expected_clusters == [area.dict() for area in clusters]

    file_tree_mock.get.side_effect = [{}, {}, {}]
    expected_all = [
        {
            "name": "a1",
            "type": AreaType.AREA,
            "metadata": {"country": "fr"},
            "set": None,
            "thermals": [],
            "id": "a1",
        },
        {
            "name": "a2",
            "type": AreaType.AREA,
            "metadata": {"country": None},
            "set": None,
            "thermals": [],
            "id": "a2",
        },
        {
            "name": "a3",
            "type": AreaType.AREA,
            "metadata": {"country": None},
            "set": None,
            "thermals": [],
            "id": "a3",
        },
        {
            "name": "s1",
            "type": AreaType.DISTRICT,
            "metadata": {"country": None},
            "set": ["a1"],
            "thermals": None,
            "id": "s1",
        },
    ]
    all = area_manager.get_all_areas(study)
    assert expected_all == [area.dict() for area in all]

    links = link_manager.get_all_links(study)
    assert [
        {
            "area1": "a1",
            "area2": "a2",
        },
        {
            "area1": "a1",
            "area2": "a3",
        },
        {
            "area1": "a2",
            "area2": "a3",
        },
    ] == [link.dict() for link in links]

    pass


def test_delete_area():
    raw_study_service = Mock(spec=RawStudyService)
    area_manager = AreaManager(
        storage_service=StudyStorageService(raw_study_service, Mock())
    )
    pass


def test_update_area():
    raw_study_service = Mock(spec=RawStudyService)
    area_manager = AreaManager(
        storage_service=StudyStorageService(raw_study_service, Mock())
    )

    study = RawStudy()
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
        sets={"s1": Set(areas=["a1"])},
    )
    raw_study_service.get_raw.return_value = FileStudy(
        config=config, tree=FileStudyTree(context=Mock(), config=config)
    )

    area_manager.patch_service = Mock()
    area_manager.patch_service.get.return_value = Patch(
        areas={"a1": PatchArea(country="fr")}
    )

    new_area_info = area_manager.update_area_metadata(
        study, "a1", PatchArea(country="fr")
    )
    assert new_area_info.id == "a1"
    assert new_area_info.metadata == {"country": "fr"}


def test_update_clusters():
    raw_study_service = Mock(spec=RawStudyService)
    area_manager = AreaManager(
        storage_service=StudyStorageService(raw_study_service, Mock())
    )

    study = RawStudy()
    config = FileStudyTreeConfig(
        study_path=Path("somepath"),
        path=Path("somepath"),
        study_id="",
        version=-1,
        areas={
            "a1": Area(
                name="a1",
                links={},
                thermals=[Cluster(id="a", name="a", enabled=True)],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            )
        },
    )
    file_tree_mock = Mock(spec=FileStudyTree, context=Mock(), config=config)
    raw_study_service.get_raw.return_value = FileStudy(
        config=config, tree=file_tree_mock
    )

    area_manager.patch_service = Mock()
    area_manager.patch_service.get.return_value = Patch(
        areas={"a1": PatchArea(country="fr")},
        thermal_clusters={"a1.a": PatchCluster.parse_obj({"code-oi": "1"})},
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

    new_area_info = area_manager.update_thermal_cluster_metadata(
        study, "a1", {"a": PatchCluster(type="a")}
    )
    assert len(new_area_info.thermals) == 1
    assert new_area_info.thermals[0].type == "a"
    assert new_area_info.thermals[0].code_oi == None

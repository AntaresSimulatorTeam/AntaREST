from pathlib import Path
from unittest.mock import Mock

from antarest.study.business.link_management import LinkManager
from antarest.study.model import RawStudy, Patch, PatchLeafDict, PatchArea
from antarest.study.business.area_management import (
    AreaManager,
    AreaType,
    AreaPatchUpdateDTO,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
    Area,
    Set,
    Link,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)
from antarest.study.storage.rawstudy.raw_study_service import (
    RawStudyService,
)


def test_create_area():
    raw_study_service = Mock(spec=RawStudyService)
    area_manager = AreaManager(raw_study_service=raw_study_service)
    pass


def test_get_all_area():
    raw_study_service = Mock(spec=RawStudyService)
    area_manager = AreaManager(raw_study_service=raw_study_service)
    link_manager = LinkManager(raw_study_service=raw_study_service)

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
                thermals=[],
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
    raw_study_service.get_raw.return_value = FileStudy(
        config=config, tree=FileStudyTree(context=Mock(), config=config)
    )

    raw_study_service.patch_service = Mock()
    raw_study_service.patch_service.get.return_value = Patch(
        areas=PatchLeafDict(a1=PatchArea(country="fr"))
    )

    expected_areas = [
        {
            "name": "a1",
            "type": AreaType.AREA,
            "metadata": {"country": "fr"},
            "set": None,
            "id": "a1",
        },
        {
            "name": "a2",
            "type": AreaType.AREA,
            "metadata": {"country": None},
            "set": None,
            "id": "a2",
        },
        {
            "name": "a3",
            "type": AreaType.AREA,
            "metadata": {"country": None},
            "set": None,
            "id": "a3",
        },
    ]
    areas = area_manager.get_all_areas(study, AreaType.AREA)
    assert expected_areas == [area.dict() for area in areas]

    expected_clusters = [
        {
            "name": "s1",
            "type": AreaType.CLUSTER,
            "metadata": {"country": None},
            "set": ["a1"],
            "id": "s1",
        }
    ]
    clusters = area_manager.get_all_areas(study, AreaType.CLUSTER)
    assert expected_clusters == [area.dict() for area in clusters]

    expected_all = [
        {
            "name": "a1",
            "type": AreaType.AREA,
            "metadata": {"country": "fr"},
            "set": None,
            "id": "a1",
        },
        {
            "name": "a2",
            "type": AreaType.AREA,
            "metadata": {"country": None},
            "set": None,
            "id": "a2",
        },
        {
            "name": "a3",
            "type": AreaType.AREA,
            "metadata": {"country": None},
            "set": None,
            "id": "a3",
        },
        {
            "name": "s1",
            "type": AreaType.CLUSTER,
            "metadata": {"country": None},
            "set": ["a1"],
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
    area_manager = AreaManager(raw_study_service=raw_study_service)
    pass


def test_update_area():
    raw_study_service = Mock(spec=RawStudyService)
    area_manager = AreaManager(raw_study_service=raw_study_service)

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

    raw_study_service.patch_service = Mock()
    raw_study_service.patch_service.get.return_value = Patch(
        areas=PatchLeafDict(a1=PatchArea(country="fr"))
    )

    raw_study_service.patch_service.patch.side_effect = lambda x, y: y

    new_area_info = area_manager.update_area(
        study,
        "a1",
        AreaPatchUpdateDTO(
            type=AreaType.AREA, metadata=PatchArea(country="fr")
        ),
    )
    assert new_area_info.id == "a1"
    assert new_area_info.metadata == {"country": "fr"}

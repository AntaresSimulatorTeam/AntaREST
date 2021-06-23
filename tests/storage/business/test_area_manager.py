import json
from pathlib import Path
from unittest.mock import Mock

from antarest.storage.business.area_management import (
    AreaManager,
    AreaType,
    AreaInfoDTO,
)
from antarest.storage.business.raw_study_service import RawStudyService
from antarest.storage.model import RawStudy, Patch, PatchLeafDict, PatchArea
from antarest.storage.repository.filesystem.config.model import (
    StudyConfig,
    Area,
    Set,
)


def test_create_area():
    raw_study_service = Mock(spec=RawStudyService)
    area_manager = AreaManager(raw_study_service=raw_study_service)
    pass


def test_get_all_area():
    raw_study_service = Mock(spec=RawStudyService)
    area_manager = AreaManager(raw_study_service=raw_study_service)

    study = RawStudy()
    config = StudyConfig(
        study_path=Path("somepath"),
        areas={
            "a1": Area({}, [], [], []),
            "a2": Area({}, [], [], []),
        },
        sets={"s1": Set(["a1"])},
    )
    raw_study_service.get_study.return_value = (config, None)

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
            "name": "s1",
            "type": AreaType.CLUSTER,
            "metadata": {"country": None},
            "set": ["a1"],
            "id": "s1",
        },
    ]
    all = area_manager.get_all_areas(study)
    assert expected_all == [area.dict() for area in all]

    pass


def test_delete_area():
    raw_study_service = Mock(spec=RawStudyService)
    area_manager = AreaManager(raw_study_service=raw_study_service)
    pass


def test_update_area():
    raw_study_service = Mock(spec=RawStudyService)
    area_manager = AreaManager(raw_study_service=raw_study_service)
    pass

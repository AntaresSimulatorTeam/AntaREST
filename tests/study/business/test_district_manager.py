from unittest.mock import Mock, patch

import pytest

from antarest.core.exceptions import (
    AreaNotFound,
    DistrictAlreadyExist,
    DistrictNotFound,
)
from antarest.study.business.district_manager import (
    DistrictInfoDTO,
    DistrictManager,
    DistrictCreationDTO,
    DistrictUpdateDTO,
)
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    DistrictSet,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command.create_district import (
    CreateDistrict,
)
from antarest.study.storage.variantstudy.model.command.remove_district import (
    RemoveDistrict,
)
from antarest.study.storage.variantstudy.model.command.update_district import (
    UpdateDistrict,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)
from antarest.study.storage.variantstudy.variant_study_service import (
    VariantStudyService,
)

# noinspection SpellCheckingInspection
EXECUTE_OR_ADD_COMMANDS = (
    "antarest.study.business.district_manager.execute_or_add_commands"
)


def _check_execute_or_add_commands(patched_func, expected_cls):
    assert patched_func.call_count == 1
    commands = patched_func.mock_calls[0].args[2]
    command = commands[0]
    assert isinstance(command, expected_cls)


class TestDistrictManager:
    @pytest.fixture(name="study_storage_service")
    def study_storage_service(self):
        """Return a mocked StudyStorageService for the DistrictManager unit tests."""
        return Mock(
            spec=StudyStorageService,
            variant_study_service=Mock(
                spec=VariantStudyService,
                command_factory=Mock(
                    spec=CommandFactory,
                    command_context=Mock(spec=CommandContext),
                ),
            ),
        )

    def test_get_districts(self, study_storage_service: StudyStorageService):
        # prepare data
        areas = dict.fromkeys(["n1", "n2", "n3"])
        sets = {
            "d1": DistrictSet(name="D1", areas=[], output=True),
            "d2": DistrictSet(name="D2", areas=["n1", "n2"], output=True),
            "d3": DistrictSet(
                name="D2", areas=["n1", "n2", "n3"], output=False
            ),
        }

        # mocks
        file_study_tree = Mock(spec=FileStudyTree)
        file_study_tree.get.return_value = {
            "comments": "dummy"
        }  # same comment for all nodes
        file_study = Mock(
            spec=FileStudy,
            config=Mock(areas=areas, sets=sets),
            tree=file_study_tree,
        )
        raw_study_service = Mock(spec=RawStudyService)
        raw_study_service.get_raw.return_value = file_study
        study_storage_service.get_storage.return_value = raw_study_service

        # run
        manager = DistrictManager(study_storage_service)
        study = Mock(spec=Study)
        actual = manager.get_districts(study)
        expected = [
            DistrictInfoDTO(
                id="d1",
                name="D1",
                areas=[],
                output=True,
                comments="dummy",
            ),
            DistrictInfoDTO(
                id="d2",
                name="D2",
                areas=["n1", "n2"],
                output=True,
                comments="dummy",
            ),
            DistrictInfoDTO(
                id="d3",
                name="D2",
                areas=["n1", "n2", "n3"],
                output=False,
                comments="dummy",
            ),
        ]
        assert actual == expected

    def test_create_district__district_already_exist(
        self, study_storage_service: StudyStorageService
    ):
        # prepare data
        areas = dict.fromkeys(["n1", "n2", "n3"])
        sets = {
            "d1": DistrictSet(name="D1", areas=[], output=True),
        }

        # mocks
        file_study = Mock(
            spec=FileStudy,
            config=Mock(areas=areas, sets=sets),
            tree=Mock(spec=FileStudyTree),
        )
        raw_study_service = Mock(spec=RawStudyService)
        raw_study_service.get_raw.return_value = file_study
        study_storage_service.get_storage.return_value = raw_study_service

        # run
        manager = DistrictManager(study_storage_service)
        study = Mock(spec=Study)
        dto = DistrictCreationDTO(
            name="d1", output=True, comments="", areas=[]
        )
        with pytest.raises(DistrictAlreadyExist):
            manager.create_district(study, dto)

    def test_create_district__area_not_found(
        self, study_storage_service: StudyStorageService
    ):
        # prepare data
        areas = dict.fromkeys(["n1", "n2", "n3"])
        sets = {}

        # mocks
        file_study = Mock(
            spec=FileStudy,
            config=Mock(areas=areas, sets=sets),
            tree=Mock(spec=FileStudyTree),
        )
        raw_study_service = Mock(spec=RawStudyService)
        raw_study_service.get_raw.return_value = file_study
        study_storage_service.get_storage.return_value = raw_study_service

        # run
        manager = DistrictManager(study_storage_service)
        study = Mock(spec=Study)
        dto = DistrictCreationDTO(
            name="d1",
            output=True,
            comments="",
            areas=["n2", "MISSING"],
        )
        with pytest.raises(AreaNotFound, match=r"MISSING"):
            manager.create_district(study, dto)

    def test_create_district__nominal(
        self, study_storage_service: StudyStorageService
    ):
        # prepare data
        areas = dict.fromkeys(["n1", "n2", "n3"])
        sets = {
            "all areas": DistrictSet(
                name="All areas", areas=["n1", "n2", "n3"], output=False
            ),
        }

        # mocks
        file_study = Mock(
            spec=FileStudy,
            config=Mock(areas=areas, sets=sets),
            tree=Mock(spec=FileStudyTree),
        )
        raw_study_service = Mock(spec=RawStudyService)
        raw_study_service.get_raw.return_value = file_study
        study_storage_service.get_storage.return_value = raw_study_service

        # run
        manager = DistrictManager(study_storage_service)
        study = Mock(spec=Study)
        dto = DistrictCreationDTO(
            name="D1",
            output=True,
            comments="hello",
            areas=["n1", "n2", "n2"],  # areas can have duplicates
        )
        with patch(EXECUTE_OR_ADD_COMMANDS) as exe:
            actual = manager.create_district(study, dto)
        expected = DistrictInfoDTO(
            id="d1",
            name="D1",
            areas=["n1", "n2"],
            output=True,
            comments="hello",
        )
        actual.areas.sort()
        assert actual == expected
        _check_execute_or_add_commands(exe, CreateDistrict)

    def test_update_district__district_not_found(
        self, study_storage_service: StudyStorageService
    ):
        # prepare data
        areas = dict.fromkeys(["n1", "n2", "n3"])
        sets = {}

        # mocks
        file_study = Mock(
            spec=FileStudy,
            config=Mock(areas=areas, sets=sets),
            tree=Mock(spec=FileStudyTree),
        )
        raw_study_service = Mock(spec=RawStudyService)
        raw_study_service.get_raw.return_value = file_study
        study_storage_service.get_storage.return_value = raw_study_service

        # run
        manager = DistrictManager(study_storage_service)
        study = Mock(spec=Study)
        dto = DistrictUpdateDTO(output=True, comments="", areas=[])
        with pytest.raises(DistrictNotFound, match="MISSING"):
            manager.update_district(study, "MISSING", dto)

    def test_update_district__area_not_found(
        self, study_storage_service: StudyStorageService
    ):
        # prepare data
        areas = dict.fromkeys(["n1", "n2", "n3"])
        sets = {
            "d1": DistrictSet(
                name="D1", areas=["n1", "n2", "n3"], output=False
            ),
        }

        # mocks
        file_study = Mock(
            spec=FileStudy,
            config=Mock(areas=areas, sets=sets),
            tree=Mock(spec=FileStudyTree),
        )
        raw_study_service = Mock(spec=RawStudyService)
        raw_study_service.get_raw.return_value = file_study
        study_storage_service.get_storage.return_value = raw_study_service

        # run
        manager = DistrictManager(study_storage_service)
        study = Mock(spec=Study)
        dto = DistrictUpdateDTO(
            output=True,
            comments="",
            areas=["n2", "MISSING"],
        )
        with pytest.raises(AreaNotFound, match=r"MISSING"):
            manager.update_district(study, "d1", dto)

    def test_update_district__nominal(
        self, study_storage_service: StudyStorageService
    ):
        # prepare data
        areas = dict.fromkeys(["n1", "n2", "n3"])
        sets = {
            "d1": DistrictSet(
                name="D1", areas=["n1", "n2", "n3"], output=False
            ),
        }

        # mocks
        file_study = Mock(
            spec=FileStudy,
            config=Mock(areas=areas, sets=sets),
            tree=Mock(spec=FileStudyTree),
        )
        raw_study_service = Mock(spec=RawStudyService)
        raw_study_service.get_raw.return_value = file_study
        study_storage_service.get_storage.return_value = raw_study_service

        # run
        manager = DistrictManager(study_storage_service)
        study = Mock(spec=Study)
        dto = DistrictUpdateDTO(
            output=True,
            comments="",
            areas=["n2", "n3"],
        )
        with patch(EXECUTE_OR_ADD_COMMANDS) as exe:
            manager.update_district(study, "d1", dto)
        _check_execute_or_add_commands(exe, UpdateDistrict)

    def test_remove_district__district_not_found(
        self, study_storage_service: StudyStorageService
    ):
        # prepare data
        areas = dict.fromkeys(["n1", "n2", "n3"])
        sets = {}

        # mocks
        file_study = Mock(
            spec=FileStudy,
            config=Mock(areas=areas, sets=sets),
            tree=Mock(spec=FileStudyTree),
        )
        raw_study_service = Mock(spec=RawStudyService)
        raw_study_service.get_raw.return_value = file_study
        study_storage_service.get_storage.return_value = raw_study_service

        # run
        manager = DistrictManager(study_storage_service)
        study = Mock(spec=Study)
        with pytest.raises(DistrictNotFound, match="MISSING"):
            manager.remove_district(study, district_id="MISSING")

    def test_remove_district__nominal(
        self, study_storage_service: StudyStorageService
    ):
        # prepare data
        areas = dict.fromkeys(["n1", "n2", "n3"])
        sets = {
            "d1": DistrictSet(
                name="D1", areas=["n1", "n2", "n3"], output=False
            ),
        }

        # mocks
        file_study = Mock(
            spec=FileStudy,
            config=Mock(areas=areas, sets=sets),
            tree=Mock(spec=FileStudyTree),
        )
        raw_study_service = Mock(spec=RawStudyService)
        raw_study_service.get_raw.return_value = file_study
        study_storage_service.get_storage.return_value = raw_study_service

        # run
        manager = DistrictManager(study_storage_service)
        study = Mock(spec=Study)
        with patch(EXECUTE_OR_ADD_COMMANDS) as exe:
            manager.remove_district(study, district_id="d1")
        _check_execute_or_add_commands(exe, RemoveDistrict)

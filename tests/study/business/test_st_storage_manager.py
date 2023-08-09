import datetime
import io
import uuid
from typing import cast
from unittest.mock import Mock

from sqlalchemy.orm.session import Session  # type: ignore

import pytest
from antarest.core.exceptions import (
    STStorageConfigNotFoundError,
    STStorageFieldsNotFoundError,
)
from antarest.core.model import PublicMode
from antarest.login.model import Group, User
from antarest.study.business.st_storage_manager import STStorageManager
from antarest.study.model import RawStudy, Study, StudyContentStatus
from antarest.study.storage.rawstudy.io.reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import (
    STStorageGroup,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import (
    FileStudyTree,
)
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)
from antarest.study.storage.variantstudy.variant_study_service import (
    VariantStudyService,
)

# noinspection SpellCheckingInspection
LIST_INI = """
[storage1]
name = Storage1
group = Battery
injectionnominalcapacity = 1500
withdrawalnominalcapacity = 1500
reservoircapacity = 20000
efficiency = 0.94
initialleveloptim = true

[storage2]
name = Storage2
group = PSP_closed
injectionnominalcapacity = 2000
withdrawalnominalcapacity = 1500
reservoircapacity = 20000
efficiency = 0.78
initiallevel = 10000

[storage3]
name = Storage3
group = PSP_closed
injectionnominalcapacity = 1500
withdrawalnominalcapacity = 1500
reservoircapacity = 21000
efficiency = 0.72
initiallevel = 20000
"""

LIST_CFG = IniReader().read(io.StringIO(LIST_INI))


class TestSTStorageManager:
    @pytest.fixture(name="study_storage_service")
    def study_storage_service(self) -> StudyStorageService:
        """Return a mocked StudyStorageService."""
        return Mock(
            spec=StudyStorageService,
            variant_study_service=Mock(
                spec=VariantStudyService,
                command_factory=Mock(
                    spec=CommandFactory,
                    command_context=Mock(spec=CommandContext),
                ),
            ),
            get_storage=Mock(
                return_value=Mock(
                    spec=RawStudyService, get_raw=Mock(spec=FileStudy)
                )
            ),
        )

    # noinspection PyArgumentList
    @pytest.fixture(name="study_uuid")
    def study_uuid_fixture(self, db_session: Session) -> str:
        user = User(id=0, name="admin")
        group = Group(id="my-group", name="group")
        raw_study = RawStudy(
            id=str(uuid.uuid4()),
            name="Dummy",
            version="850",
            author="John Smith",
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc),
            public_mode=PublicMode.FULL,
            owner=user,
            groups=[group],
            workspace="default",
            path="/path/to/study",
            content_status=StudyContentStatus.WARNING,
        )
        db_session.add(raw_study)
        db_session.commit()
        return cast(str, raw_study.id)

    def test_get_st_storages__nominal_case(
        self,
        db_session: Session,
        study_storage_service: StudyStorageService,
        study_uuid: str,
    ) -> None:
        """
        This unit test is to verify the behavior of the `get_st_storages`
        method in the `STStorageManager` class under nominal conditions.
        It checks whether the method returns the expected storage list
        based on a specific configuration.
        """
        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Prepare the mocks
        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = Mock(
            spec=FileStudyTree,
            get=Mock(return_value=LIST_CFG),
        )

        # Given the following arguments
        manager = STStorageManager(study_storage_service)

        # run
        groups = manager.get_st_storages(study, area_id="West")

        # Check
        actual = [form.dict(by_alias=True) for form in groups]
        expected = [
            {
                "efficiency": 0.94,
                "group": STStorageGroup.BATTERY,
                "id": "storage1",
                "initialLevel": 0.0,
                "initialLevelOptim": True,
                "injectionNominalCapacity": 1500.0,
                "name": "Storage1",
                "reservoirCapacity": 20000.0,
                "withdrawalNominalCapacity": 1500.0,
            },
            {
                "efficiency": 0.78,
                "group": STStorageGroup.PSP_CLOSED,
                "id": "storage2",
                "initialLevel": 10000.0,
                "initialLevelOptim": False,
                "injectionNominalCapacity": 2000.0,
                "name": "Storage2",
                "reservoirCapacity": 20000.0,
                "withdrawalNominalCapacity": 1500.0,
            },
            {
                "efficiency": 0.72,
                "group": STStorageGroup.PSP_CLOSED,
                "id": "storage3",
                "initialLevel": 20000.0,
                "initialLevelOptim": False,
                "injectionNominalCapacity": 1500.0,
                "name": "Storage3",
                "reservoirCapacity": 21000.0,
                "withdrawalNominalCapacity": 1500.0,
            },
        ]
        assert actual == expected

    def test_get_st_storages__config_not_found(
        self,
        db_session: Session,
        study_storage_service: StudyStorageService,
        study_uuid: str,
    ) -> None:
        """
        This test verifies that when the `get_st_storages` method is called
        with a study and area ID, and the corresponding configuration is not found
        (indicated by the `KeyError` raised by the mock), it correctly
        raises the `STStorageConfigNotFoundError` exception with the expected error
        message containing the study ID and area ID.
        """
        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Prepare the mocks
        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = Mock(
            spec=FileStudyTree,
            get=Mock(side_effect=KeyError("Oops!")),
        )

        # Given the following arguments
        manager = STStorageManager(study_storage_service)

        # run
        with pytest.raises(
            STStorageConfigNotFoundError, match="missing configuration"
        ) as ctx:
            manager.get_st_storages(study, area_id="West")

        # ensure the error message contains at least the study ID and area ID
        err_msg = str(ctx.value)
        assert study.id in err_msg
        assert "West" in err_msg

    def test_get_st_storage__nominal_case(
        self,
        db_session: Session,
        study_storage_service: StudyStorageService,
        study_uuid: str,
    ) -> None:
        """
        Test the `get_st_storage` method of the `STStorageManager` class under nominal conditions.

        This test verifies that the `get_st_storage` method returns the expected storage fields
        for a specific study, area, and storage ID combination.

        Args:
            db_session: A database session fixture.
            study_storage_service: A study storage service fixture.
            study_uuid: The UUID of the study to be tested.
        """

        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Prepare the mocks
        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = Mock(
            spec=FileStudyTree,
            get=Mock(return_value=LIST_CFG["storage1"]),
        )

        # Given the following arguments
        manager = STStorageManager(study_storage_service)

        # Run the method being tested
        edit_form = manager.get_st_storage(
            study, area_id="West", storage_id="storage1"
        )

        # Assert that the returned storage fields match the expected fields
        actual = edit_form.dict(by_alias=True)
        expected = {
            "efficiency": 0.94,
            "group": STStorageGroup.BATTERY,
            "id": "storage1",
            "initialLevel": 0.0,
            "initialLevelOptim": True,
            "injectionNominalCapacity": 1500.0,
            "name": "Storage1",
            "reservoirCapacity": 20000.0,
            "withdrawalNominalCapacity": 1500.0,
        }
        assert actual == expected

    def test_get_st_storage__config_not_found(
        self,
        db_session: Session,
        study_storage_service: StudyStorageService,
        study_uuid: str,
    ) -> None:
        """
        Test the `get_st_storage` method of the `STStorageManager` class when the configuration is not found.

        This test verifies that the `get_st_storage` method raises an `STStorageFieldsNotFoundError`
        exception when the configuration for the provided study, area, and storage ID combination is not found.

        Args:
            db_session: A database session fixture.
            study_storage_service: A study storage service fixture.
            study_uuid: The UUID of the study to be tested.
        """

        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Prepare the mocks
        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = Mock(
            spec=FileStudyTree,
            get=Mock(side_effect=KeyError("Oops!")),
        )

        # Given the following arguments
        manager = STStorageManager(study_storage_service)

        # Run the method being tested and expect an exception
        with pytest.raises(
            STStorageFieldsNotFoundError, match="not found"
        ) as ctx:
            manager.get_st_storage(
                study, area_id="West", storage_id="storage1"
            )
        # ensure the error message contains at least the study ID, area ID and storage ID
        err_msg = str(ctx.value)
        assert study.id in err_msg
        assert "West" in err_msg
        assert "storage1" in err_msg

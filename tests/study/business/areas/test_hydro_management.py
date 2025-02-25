import datetime
from pathlib import Path
from typing import Tuple
from unittest.mock import Mock

from antarest.core.config import Config
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.model import PublicMode
from antarest.core.tasks.service import TaskJobService
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import User
from antarest.login.service import LoginService
from antarest.study.business.areas.hydro_management import ManagementOptionsFormFields
from antarest.study.business.model.area_model import AreaCreationDTO, AreaType
from antarest.study.model import RawStudy
from antarest.study.repository import StudyMetadataRepository
from antarest.study.service import StudyService
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from tests.helpers import with_db_context


class TestHydroManagement:
    """ """
    @staticmethod
    def setup(
        raw_study_service: RawStudyService,
        variant_study_service: VariantStudyService,
        tmp_path: Path,
        task_service: TaskJobService,
        core_cache: ICache,
        event_bus: IEventBus
    ) -> Tuple[RawStudy, StudyService]:
        """
        Set up data for the next tests
        - Create a raw study
        - Initialize a study service
        - Create an area in this study
        """
        # create a raw study
        user = User(id=30, name="regular")
        db.session.add(user)

        path = tmp_path / "area_test_study"
        raw_study = RawStudy(
            id="my_raw_study",
            name=path.name,
            version="860",
            author="John Smith",
            public_mode=PublicMode.FULL,
            owner=user,
            path=str(path),
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
        )
        db.session.add(raw_study)

        db.session.commit()

        raw_study = raw_study_service.create(raw_study)

        # Initialize a study service
        repository = StudyMetadataRepository(core_cache)
        study_service = StudyService(
            raw_study_service=raw_study_service,
            variant_study_service=variant_study_service,
            user_service=Mock(spec=LoginService),
            repository=repository,
            event_bus=event_bus,
            task_service=task_service,
            file_transfer_manager=Mock(spec=FileTransferManager),
            cache_service=core_cache,
            config=Mock(spec=Config),
        )

        return raw_study, study_service

    @with_db_context
    def test_get_field_values(
        self,
        raw_study_service: RawStudyService,
        variant_study_service: VariantStudyService,
        tmp_path: Path,
        task_service: TaskJobService,
        core_cache: ICache,
        event_bus: IEventBus
    ):
        """
        Create an area, edit manually some fields with capital letters
        Check if data retrieved match the original files
        """
        # retrieve setup data
        raw_study, study_service = self.setup(
            raw_study_service,
            variant_study_service,
            tmp_path,
            task_service,
            core_cache,
            event_bus
        )
        # create an area
        area_creation_dto = AreaCreationDTO(name="AreaTestGet", type=AreaType.AREA)
        area = study_service.area_manager.create_area(raw_study, area_creation_dto)
        path = Path(raw_study.path)

        # gather initial data of the area
        initial_data = study_service.hydro_manager.get_field_values(raw_study, area.id)

        # change `area_id` case and edit one field (inter-daily-breakdown)
        hydro_ini_path = path.joinpath("input/hydro/hydro.ini")
        with open(hydro_ini_path) as f:
            old_content = f.read()
            new_content = old_content.replace("areatestget", "AreaTestGet").replace(
                "[inter-daily-breakdown]\n" "AreaTestGet = 1",
                "[inter-daily-breakdown]\n" "AreaTestGet = 2",
            )

        with open(hydro_ini_path, "w") as f:
            f.write(new_content)

        # retrieve new values
        new_data = study_service.hydro_manager.get_field_values(raw_study, area.id)

        # if `get_fields_values` returns correct values, it must differ from its previous version
        assert new_data != initial_data

    @with_db_context
    def test_set_field_values(
        self,
        raw_study_service: RawStudyService,
        variant_study_service: VariantStudyService,
        tmp_path: Path,
        task_service: TaskJobService,
        core_cache: ICache,
        event_bus: IEventBus
    ):
        """
        Test if set_field_values works as expected
        Modify some fields
        """
        # retrieve setup data
        raw_study, study_service = self.setup(
            raw_study_service,
            variant_study_service,
            tmp_path,
            task_service,
            core_cache,
            event_bus
        )
        # create an area
        area_creation_dto = AreaCreationDTO(name="AreaTestSet", type=AreaType.AREA)
        area = study_service.area_manager.create_area(raw_study, area_creation_dto)
        path = Path(raw_study.path)

        # gather initial data
        initial_data = study_service.hydro_manager.get_field_values(raw_study, area.id).dict()

        # set area id with capital letters
        hydro_ini_path = path.joinpath("input/hydro/hydro.ini")
        with open(hydro_ini_path) as f:
            old_content = f.read()
            new_content = old_content.replace("areatestset", "AreaTestSet")

        with open(hydro_ini_path, "w") as f:
            f.write(new_content)

        # set multiple values with set_field_values
        new_field_values = ManagementOptionsFormFields(**{"inter_daily_breakdown": 5, "reservoir": True})
        study_service.hydro_manager.set_field_values(raw_study, new_field_values, area.id)

        # retrieve new values
        new_data = study_service.hydro_manager.get_field_values(raw_study, area.id).dict()

        assert new_data != initial_data

        for field_name, value in new_data.items():
            # fields that were modified must retrieve different values
            if field_name in ["inter_daily_breakdown", "reservoir"]:
                assert value != initial_data[field_name]
            # fields that were not must be the same
            else:
                assert value == initial_data[field_name]

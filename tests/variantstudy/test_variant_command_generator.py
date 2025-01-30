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
import datetime
import logging
import pytest
import uuid
from pathlib import Path
from unittest.mock import Mock

from antarest.core.config import Config
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import IEventBus
from antarest.core.jwt import JWTUser
from antarest.core.model import PublicMode
from antarest.core.requests import RequestParameters
from antarest.core.tasks.service import TaskJobService
from antarest.login.model import User, Group
from antarest.login.service import LoginService
from antarest.login.utils import current_user_context
from antarest.study.business.area_management import AreaCreationDTO, AreaType, AreaManager
from antarest.study.business.general_management import GeneralFormFields, Mode, Month, BuildingMode, WeekDay
from antarest.study.model import RawStudy, StudyAdditionalData, CommentsDto, StudyMetadataPatchDTO, PatchArea
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.repository import StudyMetadataRepository
from antarest.study.service import StudyService
from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.business.utils import transform_command_to_dto
from antarest.study.storage.variantstudy.model.command.update_raw_file import UpdateRawFile
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.repository import VariantStudyRepository
from antarest.study.storage.variantstudy.variant_command_generator import VariantCommandGenerator
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from tests.conftest_services import task_service_fixture
from tests.helpers import with_db_context
from tests.storage.integration.conftest import storage_service


logger = logging.getLogger(__name__)

class TestVariantCommandGenerator:
    """

    """
    @with_db_context
    def test_generate(
            self,
            caplog,
            tmp_path: Path,
            variant_study_service: VariantStudyService,
            variant_study_repository: VariantStudyRepository,
            task_service: TaskJobService,
            core_cache: ICache,
            event_bus: IEventBus,
            raw_study_service,
            generator_matrix_constants,
            simple_matrix_service,
            patch_service
    ):
        """
        Set Up:
            Create a raw study, create a variant study, add some commands to it.
        Test:
            - Check if the generated commands does not return an error with the notifier.
            - Check whether the _generate() method get a flatten list of commands, without
              any block of commands.
        """
        # variant_study_service.generator = VariantCommandGenerator(variant_study_service.study_factory)
        user = User(id=32, name="Tester")
        db.session.add(user)
        db.session.commit()
        jwt_user = Mock(spec=JWTUser, id=user.id, impersonator=user.id, is_site_admin=Mock(return_value=True))
        params = Mock(spec=RequestParameters, user=jwt_user)

        group = Group(id="test", name="test")
        db.session.add(group)
        db.session.commit()

        path = tmp_path / "testing-study"
        root_study = RawStudy(
            id=str(uuid.uuid4()),
            name="Test Raw Study",
            version="860",
            author=user.name,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
            public_mode=PublicMode.FULL,
            owner=user,
            groups=[group],
            path=str(path),
            additional_data=StudyAdditionalData(author=user.name),
        )
        db.session.add(root_study)
        db.session.commit()

        raw_study_service.create(root_study)

        variant_study = variant_study_service.create_variant_study(
            root_study.id,
            "Variant study",
            params
        )

        # file_study = variant_study_service.get_raw(variant_study)
        #
        # command_context = CommandContext(
        #     generator_matrix_constants=generator_matrix_constants,
        #     matrix_service=simple_matrix_service,
        #     patch_service=patch_service,
        # )

        study_service = StudyService(
            raw_study_service=raw_study_service,
            variant_study_service=variant_study_service,
            user_service=Mock(spec=LoginService),
            repository=variant_study_repository,
            event_bus=event_bus,
            task_service=task_service,
            file_transfer_manager=Mock(spec=FileTransferManager),
            cache_service=core_cache,
            config=Mock(spec=Config),
        )

        # add some commands
        ## add comments
        comments_dto = CommentsDto(
            comments="add some comments"
        )
        study_service.edit_comments(variant_study.id, comments_dto, params)

        ## create an area
        area_manager = AreaManager(
            Mock(spec=StudyStorageService),
            Mock(spec=StudyMetadataRepository)
        )

        area_creation_dto = AreaCreationDTO(
            name="area_test",
            type=AreaType.AREA,
        )

        ## add a command with multiple sub commands
        general_form_fields = GeneralFormFields(
            mode=Mode.ECONOMY,
            first_day=3,
            last_day=365,
            horizon="2028-2029",
            first_month=Month.JANUARY,
            first_week_day=WeekDay.MONDAY,
            first_january=WeekDay.WEDNESDAY,
            leap_year=True,
            nb_years=1,
            building_mode=BuildingMode.AUTOMATIC,
            selection_mode=True,
            year_by_year=True,
            simulation_synthesis=False,
            mc_scenario=False,
            filtering=False,
            geographic_trimming=False,
            thematic_trimming=False
        )
        with current_user_context(token=jwt_user):
            new_area = study_service.create_area(variant_study.id, area_creation_dto, params)
            study_service.general_manager.set_field_values(variant_study, general_form_fields)

        # at this point, the command must have 3 command block and more regarding all commands
        assert len(variant_study_service.get_commands(variant_study.id, params)) == 3

        # the call to generate_study_config must not add
        # an error log such as "fail to notify command ..."
        with caplog.at_level(logging.ERROR, logger=logger.name):
            result = variant_study_service.generate_study_config(
                variant_study.id,
                params
            )

            log_records = caplog.records
            assert len(log_records) == 0

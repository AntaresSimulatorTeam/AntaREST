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
import re
import typing
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest
from antares.study.version import StudyVersion

from antarest.core.jwt import DEFAULT_ADMIN_USER, JWTUser
from antarest.core.model import PublicMode
from antarest.core.requests import RequestParameters, UserHasNotPermissionError
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import sanitize_uuid
from antarest.login.model import ADMIN_ID, ADMIN_NAME, Group, User
from antarest.login.utils import current_user_context
from antarest.matrixstore.service import SimpleMatrixService
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import RawStudy, StudyAdditionalData
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import (
    STStorageConfig,
    STStorageGroup,
    STStorageProperties,
)
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_st_storage import CreateSTStorage
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from tests.helpers import with_db_context

# noinspection SpellCheckingInspection
EXPECTED_DENORMALIZED = {
    "Desktop.ini",
    "input/areas/fr/adequacy_patch.ini",
    "input/areas/fr/optimization.ini",
    "input/areas/fr/ui.ini",
    "input/areas/list.txt",
    "input/areas/sets.ini",
    "input/bindingconstraints/bindingconstraints.ini",
    "input/hydro/allocation/fr.ini",
    "input/hydro/common/capacity/creditmodulations_fr.txt.link",
    "input/hydro/common/capacity/inflowPattern_fr.txt.link",
    "input/hydro/common/capacity/maxpower_fr.txt.link",
    "input/hydro/common/capacity/reservoir_fr.txt.link",
    "input/hydro/common/capacity/waterValues_fr.txt.link",
    "input/hydro/hydro.ini",
    "input/hydro/prepro/correlation.ini",
    "input/hydro/prepro/fr/energy.txt.link",
    "input/hydro/prepro/fr/prepro.ini",
    "input/hydro/series/fr/mingen.txt.link",
    "input/hydro/series/fr/mod.txt.link",
    "input/hydro/series/fr/ror.txt.link",
    "input/links/fr/properties.ini",
    "input/load/prepro/correlation.ini",
    "input/load/prepro/fr/conversion.txt.link",
    "input/load/prepro/fr/data.txt.link",
    "input/load/prepro/fr/k.txt.link",
    "input/load/prepro/fr/settings.ini",
    "input/load/prepro/fr/translation.txt.link",
    "input/load/series/load_fr.txt.link",
    "input/misc-gen/miscgen-fr.txt.link",
    "input/renewables/clusters/fr/list.ini",
    "input/reserves/fr.txt.link",
    "input/solar/prepro/correlation.ini",
    "input/solar/prepro/fr/conversion.txt.link",
    "input/solar/prepro/fr/data.txt.link",
    "input/solar/prepro/fr/k.txt.link",
    "input/solar/prepro/fr/settings.ini",
    "input/solar/prepro/fr/translation.txt.link",
    "input/solar/series/solar_fr.txt.link",
    "input/st-storage/clusters/fr/list.ini",
    "input/st-storage/series/fr/storage1/PMAX-injection.txt.link",
    "input/st-storage/series/fr/storage1/PMAX-withdrawal.txt.link",
    "input/st-storage/series/fr/storage1/inflows.txt.link",
    "input/st-storage/series/fr/storage1/lower-rule-curve.txt.link",
    "input/st-storage/series/fr/storage1/upper-rule-curve.txt.link",
    "input/thermal/areas.ini",
    "input/thermal/clusters/fr/list.ini",
    "input/wind/prepro/correlation.ini",
    "input/wind/prepro/fr/conversion.txt.link",
    "input/wind/prepro/fr/data.txt.link",
    "input/wind/prepro/fr/k.txt.link",
    "input/wind/prepro/fr/settings.ini",
    "input/wind/prepro/fr/translation.txt.link",
    "input/wind/series/wind_fr.txt.link",
    "layers/layers.ini",
    "settings/comments.txt",
    "settings/generaldata.ini",
    "settings/resources/study.ico",
    "settings/scenariobuilder.dat",
    "study.antares",
}


class TestVariantStudyService:
    @pytest.mark.parametrize(
        "denormalize",
        [
            pytest.param(True, id="denormalize_yes"),
            pytest.param(False, id="denormalize_no"),
        ],
    )
    @pytest.mark.parametrize(
        "from_scratch",
        [
            pytest.param(True, id="from_scratch__yes"),
            pytest.param(False, id="from_scratch__no"),
        ],
    )
    @with_db_context
    def test_generate_task(
        self,
        tmp_path: Path,
        variant_study_service: VariantStudyService,
        raw_study_service: RawStudyService,
        simple_matrix_service: SimpleMatrixService,
        generator_matrix_constants: GeneratorMatrixConstants,
        patch_service: PatchService,
        study_storage_service: StudyStorageService,
        # pytest parameters
        denormalize: bool,
        from_scratch: bool,
    ) -> None:
        ## Prepare database objects
        # noinspection PyArgumentList
        user = User(id=1, name="admin")
        db.session.add(user)
        db.session.commit()

        # define user token
        jwt_user = Mock(spec=JWTUser, id=user.id, impersonator=user.id, is_site_admin=Mock(return_value=True))

        # noinspection PyArgumentList
        group = Group(id="my-group", name="group")
        db.session.add(group)
        db.session.commit()

        ## First create a raw study (root of the variant)
        raw_study_path = tmp_path / "My RAW Study"
        # noinspection PyArgumentList
        raw_study = RawStudy(
            id="my_raw_study",
            name=raw_study_path.name,
            version="860",
            author="John Smith",
            created_at=datetime.datetime(2023, 7, 15, 16, 45),
            updated_at=datetime.datetime(2023, 7, 19, 8, 15),
            last_access=datetime.datetime.utcnow(),
            public_mode=PublicMode.FULL,
            owner=user,
            groups=[group],
            path=str(raw_study_path),
            additional_data=StudyAdditionalData(author="John Smith"),
        )
        db.session.add(raw_study)
        db.session.commit()

        ## Prepare the RAW Study
        raw_study_service.create(raw_study)
        study_version = StudyVersion.parse(raw_study.version)

        variant_study = variant_study_service.create_variant_study(
            raw_study.id,
            "My Variant Study",
            params=Mock(
                spec=RequestParameters,
                user=jwt_user,
            ),
        )

        ## Prepare the RAW Study
        file_study = variant_study_service.get_raw(variant_study)

        command_context = CommandContext(
            generator_matrix_constants=generator_matrix_constants,
            matrix_service=simple_matrix_service,
            patch_service=patch_service,
        )

        create_area_fr = CreateArea(command_context=command_context, area_name="fr", study_version=study_version)

        ## Prepare the Variant Study Data
        # noinspection SpellCheckingInspection
        pmax_injection = np.random.rand(8760, 1)
        inflows = np.random.uniform(0, 1000, size=(8760, 1))

        # noinspection PyArgumentList,PyTypeChecker
        create_st_storage = CreateSTStorage(
            command_context=command_context,
            area_id="fr",
            parameters=STStorageProperties(
                name="Storage1",
                group=STStorageGroup.BATTERY,
                injection_nominal_capacity=1500,
                withdrawal_nominal_capacity=1500,
                reservoir_capacity=20000,
                efficiency=0.94,
                initial_level_optim=True,
            ),
            pmax_injection=pmax_injection.tolist(),
            inflows=inflows.tolist(),
            study_version=study_version,
        )

        with current_user_context(jwt_user):
            execute_or_add_commands(
                variant_study,
                file_study,
                commands=[create_area_fr, create_st_storage],
                storage_service=study_storage_service,
            )

        ## Run the "generate" task
        actual_uui = variant_study_service.generate_task(
            variant_study,
            denormalize=denormalize,
            from_scratch=from_scratch,
        )
        assert re.fullmatch(
            r"[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}",
            actual_uui,
            flags=re.IGNORECASE,
        )

        ## Collect the resulting files
        workspaces = variant_study_service.config.storage.workspaces
        internal_studies_dir: Path = workspaces["default"].path
        snapshot_dir = internal_studies_dir.joinpath(variant_study.snapshot.id, "snapshot")
        res_study_files = {study_file.relative_to(snapshot_dir).as_posix() for study_file in snapshot_dir.rglob("*.*")}

        if denormalize:
            expected = {f.replace(".link", "") for f in EXPECTED_DENORMALIZED}
        else:
            expected = EXPECTED_DENORMALIZED
        assert res_study_files == expected

    @with_db_context
    def test_clear_all_snapshots(
        self,
        tmp_path: Path,
        variant_study_service: VariantStudyService,
        raw_study_service: RawStudyService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        - Test return value in case the user is not allowed to call the function,
        - Test return value in case the user give a bad argument (negative
        integer or other type than integer)
        - Test deletion of an old snapshot and a recent one

        In order to test date and time of objects, a FakeDateTime class is defined and used
        by a monkeypatch context
        """

        class FakeDatetime:
            """
            Class that handle fake timestamp creation/update of variant
            """

            fake_time: datetime.datetime

            @classmethod
            def now(cls) -> datetime.datetime:
                """Method used to get the custom timestamp"""
                return datetime.datetime(2023, 12, 31)

            @classmethod
            def utcnow(cls) -> datetime.datetime:
                """Method used while a variant is created"""
                return cls.now()

        # =============================
        #  SET UP
        # =============================
        # Create two users
        # an admin user
        # noinspection PyArgumentList
        admin_user = User(id=ADMIN_ID, name=ADMIN_NAME)
        db.session.add(admin_user)
        db.session.commit()

        regular_user = User(id=99, name="regular")
        db.session.add(regular_user)
        db.session.commit()

        # noinspection PyArgumentList
        group = Group(id="my-group", name="group")
        db.session.add(group)
        db.session.commit()

        # Create a raw study (root of the variant)
        raw_study_path = tmp_path / "My RAW Study"
        # noinspection PyArgumentList
        raw_study = RawStudy(
            id="my_raw_study",
            name=raw_study_path.name,
            version="860",
            author="John Smith",
            created_at=datetime.datetime(2023, 7, 15, 16, 45),
            updated_at=datetime.datetime(2023, 7, 19, 8, 15),
            last_access=datetime.datetime.utcnow(),
            public_mode=PublicMode.FULL,
            owner=admin_user,
            groups=[group],
            path=str(raw_study_path),
            additional_data=StudyAdditionalData(author="John Smith"),
        )

        db.session.add(raw_study)
        db.session.commit()

        # Set up the Raw Study
        raw_study_service.create(raw_study)

        # Variant studies
        variant_list = []

        # For each variant created
        with monkeypatch.context() as m:
            # Set the system date older to create older variants
            m.setattr("antarest.study.storage.variantstudy.variant_study_service.datetime", FakeDatetime)
            m.setattr("antarest.study.service.datetime", FakeDatetime)

            for index in range(3):
                variant_list.append(
                    variant_study_service.create_variant_study(
                        raw_study.id,
                        "Variant{}".format(str(index)),
                        params=Mock(
                            spec=RequestParameters,
                            user=DEFAULT_ADMIN_USER,
                        ),
                    )
                )

                # Generate a snapshot for each variant
                variant_study_service.generate(
                    sanitize_uuid(variant_list[index].id),
                    False,
                    False,
                    params=Mock(
                        spec=RequestParameters,
                        user=Mock(spec=JWTUser, id=regular_user.id, impersonator=regular_user.id),
                    ),
                )

                variant_study_service.get(variant_list[index])

        variant_study_path = Path(tmp_path).joinpath("internal_studies")

        # Check if everything was correctly initialized
        assert len(list(variant_study_path.iterdir())) == 3

        for variant in variant_study_path.iterdir():
            assert variant.is_dir()
            assert list(variant.iterdir())[0].name == "snapshot"

        # =============================
        #  TEST
        # =============================
        # A user without rights cannot clear snapshots
        with pytest.raises(UserHasNotPermissionError):
            variant_study_service.clear_all_snapshots(
                datetime.timedelta(1),
                params=Mock(
                    spec=RequestParameters,
                    user=Mock(
                        spec=JWTUser,
                        id=regular_user.id,
                        is_site_admin=Mock(return_value=False),
                        is_admin_token=Mock(return_value=False),
                    ),
                ),
            )

        # At this point, variants was not accessed yet
        # Thus snapshot directories must exist still
        for variant in variant_study_path.iterdir():
            assert variant.is_dir()
            assert list(variant.iterdir())

        # Simulate access for two old snapshots
        variant_list[0].last_access = datetime.datetime.utcnow() - datetime.timedelta(days=60)
        variant_list[1].last_access = datetime.datetime.utcnow() - datetime.timedelta(hours=6)

        # Simulate access for a recent one
        variant_list[2].last_access = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        db.session.commit()

        # Clear old snapshots
        task_id = variant_study_service.clear_all_snapshots(
            datetime.timedelta(hours=5),
            Mock(
                spec=RequestParameters,
                user=DEFAULT_ADMIN_USER,
            ),
        )
        variant_study_service.task_service.await_task(task_id)

        # Check if old snapshots was successfully cleared
        nb_snapshot_dir = 0  # after the for iterations, must equal 1
        for variant_path in variant_study_path.iterdir():
            if variant_path.joinpath("snapshot").exists():
                nb_snapshot_dir += 1
        assert nb_snapshot_dir == 1

        # Clear most recent snapshots
        task_id = variant_study_service.clear_all_snapshots(
            datetime.timedelta(hours=-1),
            Mock(
                spec=RequestParameters,
                user=DEFAULT_ADMIN_USER,
            ),
        )
        variant_study_service.task_service.await_task(task_id)

        # Check if all snapshots were cleared
        nb_snapshot_dir = 0  # after the for iterations, must equal 0
        for variant_path in variant_study_path.iterdir():
            assert not variant_path.joinpath("snapshot").exists()

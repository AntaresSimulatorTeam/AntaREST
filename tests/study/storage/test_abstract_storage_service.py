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
from pathlib import Path

from py7zr import SevenZipFile

from antarest.core.model import PublicMode
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import Group, User
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from tests.helpers import create_study, with_db_context


class TestAbstractStorageService:
    @with_db_context
    def test_export_study(self, tmp_path: Path, raw_study_service: RawStudyService) -> None:
        """
        Test the `export_study` method of the `AbstractStorageService` class.
        Args:
            tmp_path: The temporary directory where to store the 7z file.
            raw_study_service: The `RawStudyService` instance to test the `export_study` method.

        Returns:

        """
        # Prepare a dummy study with a `study.antares` file, and non-empty input and output folder
        study_path = tmp_path / "My Study"
        study_path.mkdir()
        content_list = ["study.antares", "input/areas/foo.ini", "output/20240424-1200eco/result.log"]
        for content in content_list:
            study_path.joinpath(content).parent.mkdir(parents=True, exist_ok=True)
            study_path.joinpath(content).touch()

        # noinspection PyArgumentList
        user = User(id=0, name="admin")
        db.session.add(user)
        db.session.commit()
        # noinspection PyArgumentList
        group = Group(id="my-group", name="group")
        db.session.add(group)
        db.session.commit()
        # noinspection PyArgumentList
        metadata = create_study(
            name="My Study",
            version="860",
            author="John Smith",
            created_at=datetime.datetime(2023, 7, 19, 16, 45),
            updated_at=datetime.datetime(2023, 7, 27, 8, 15),
            last_access=datetime.datetime.utcnow(),
            public_mode=PublicMode.FULL,
            owner=user,
            groups=[group],
            path=str(study_path),
        )
        db.session.add(metadata)
        db.session.commit()
        db.session.refresh(metadata)

        # Check the `export_study` function
        target_path = tmp_path / "export.7z"
        actual = raw_study_service.export_study(metadata, target_path, outputs=True)
        assert actual == target_path

        # Check that the 7zip file exist and is valid
        with SevenZipFile(target_path) as szf:
            # Check that the content of the 7z file is the same as the study folder
            assert set(content_list) == (
                set(szf.getnames())
                - {
                    ".",
                    "input",
                    "output",
                    "input/areas",
                    "output/20240424-1200eco",
                }
            )

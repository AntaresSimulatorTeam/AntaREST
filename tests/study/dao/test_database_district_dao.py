# Copyright (c) 2026, RTE (https://www.rte-france.com)
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

"""
Unit tests for DatabaseDistrictDao.
"""

import uuid

import pytest
from sqlalchemy.orm import Session

from antarest.core.exceptions import AreaNotFound, DistrictConfigNotFound
from antarest.study.business.model.district_model import District, DistrictApplyFilter
from antarest.study.dao.database.database_area_dao import DatabaseAreaDao
from antarest.study.dao.database.database_district_dao import DatabaseDistrictDao
from antarest.study.model import StorageMode
from tests.helpers import create_study


class TestDatabaseDistrictDao:
    @pytest.fixture
    def study_id(self, db_session: Session) -> str:
        study_id = str(uuid.uuid4())
        with db_session:
            study = create_study(id=study_id, name="Test Study")
            study.storage_mode = StorageMode.DATABASE
            db_session.add(study)
            db_session.commit()
        return study_id

    @pytest.fixture
    def dao(self, db_session: Session, study_id: str) -> DatabaseDistrictDao:
        return DatabaseDistrictDao(study_id, db_session)

    @pytest.fixture
    def area_dao(self, db_session: Session, study_id: str) -> DatabaseAreaDao:
        return DatabaseAreaDao(study_id, db_session)

    def test_save_district_creates_district(self, db_session: Session, dao: DatabaseDistrictDao) -> None:
        with db_session:
            district = District(id="d1", name="District 1", output=True, comments="test")
            dao.save_district(district)
            db_session.commit()

        with db_session:
            result = dao.get_district("d1")
            assert result.id == "d1"
            assert result.name == "District 1"
            assert result.output is True
            assert result.comments == "test"

    def test_save_district_with_areas(
        self, db_session: Session, dao: DatabaseDistrictDao, area_dao: DatabaseAreaDao
    ) -> None:
        with db_session:
            area_dao.save_area("Paris")
            area_dao.save_area("London")
            db_session.commit()

        with db_session:
            district = District(id="d1", name="District 1", add_areas=["paris", "london"])
            dao.save_district(district)
            db_session.commit()

        with db_session:
            result = dao.get_district("d1")
            assert set(result.add_areas) == {"paris", "london"}

    def test_save_district_raises_on_invalid_area(self, db_session: Session, dao: DatabaseDistrictDao) -> None:
        with db_session:
            district = District(id="d1", name="District 1", add_areas=["nonexistent"])
            with pytest.raises(AreaNotFound):
                dao.save_district(district)

    def test_save_district_overwrites_existing(self, db_session: Session, dao: DatabaseDistrictDao) -> None:
        with db_session:
            dao.save_district(District(id="d1", name="District 1", comments="v1"))
            db_session.commit()

        with db_session:
            dao.save_district(District(id="d1", name="District 1", comments="v2"))
            db_session.commit()

        with db_session:
            result = dao.get_district("d1")
            assert result.comments == "v2"

    def test_remove_district(self, db_session: Session, dao: DatabaseDistrictDao) -> None:
        with db_session:
            dao.save_district(District(id="d1", name="District 1"))
            db_session.commit()

        with db_session:
            dao.remove_district("d1")
            db_session.commit()

        with db_session:
            assert not dao.district_exists("d1")

    def test_get_districts_returns_all(self, db_session: Session, dao: DatabaseDistrictDao) -> None:
        with db_session:
            dao.save_district(District(id="d1", name="District 1"))
            dao.save_district(District(id="d2", name="District 2"))
            db_session.commit()

        with db_session:
            districts = dao.get_districts()
            assert len(districts) == 2
            assert {d.id for d in districts} == {"d1", "d2"}

    def test_get_district_raises_if_not_found(self, db_session: Session, dao: DatabaseDistrictDao) -> None:
        with db_session:
            with pytest.raises(DistrictConfigNotFound):
                dao.get_district("nonexistent")

    def test_district_exists(self, db_session: Session, dao: DatabaseDistrictDao) -> None:
        with db_session:
            assert not dao.district_exists("d1")
            dao.save_district(District(id="d1", name="District 1"))
            db_session.commit()

        with db_session:
            assert dao.district_exists("d1")

    def test_save_district_with_apply_filter(
        self, db_session: Session, dao: DatabaseDistrictDao, area_dao: DatabaseAreaDao
    ) -> None:
        with db_session:
            area_dao.save_area("Paris")
            db_session.commit()

        with db_session:
            district = District(
                id="d1",
                name="District 1",
                apply_filter=DistrictApplyFilter.add_all,
                subtract_areas=["paris"],
            )
            dao.save_district(district)
            db_session.commit()

        with db_session:
            result = dao.get_district("d1")
            assert result.apply_filter == DistrictApplyFilter.add_all
            assert result.subtract_areas == ["paris"]

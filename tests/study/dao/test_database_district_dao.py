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
from antarest.study.dao.database.database_district_dao import DatabaseDistrictDao
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
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
    def study_dao(self, db_session: Session, study_id: str) -> DatabaseStudyDao:
        return DatabaseStudyDao(study_id, db_session)

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
        self, db_session: Session, dao: DatabaseDistrictDao, study_dao: DatabaseStudyDao
    ) -> None:
        with db_session:
            study_dao.save_area("Paris")
            study_dao.save_area("London")
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
        self, db_session: Session, dao: DatabaseDistrictDao, study_dao: DatabaseStudyDao
    ) -> None:
        with db_session:
            study_dao.save_area("Paris")
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

    def test_delete_area_removes_area_from_districts(
        self, db_session: Session, dao: DatabaseDistrictDao, study_dao: DatabaseStudyDao
    ) -> None:
        """When an area is deleted, it should be removed from districts that reference it."""
        with db_session:
            study_dao.save_area("Paris")
            study_dao.save_area("London")
            db_session.commit()

        with db_session:
            # Create districts that reference Paris
            dao.save_district(District(id="d1", name="District 1", add_areas=["paris"]))
            dao.save_district(District(id="d2", name="District 2", add_areas=["paris", "london"]))
            # Create a district that doesn't reference Paris
            dao.save_district(District(id="d3", name="District 3", add_areas=["london"]))
            db_session.commit()

        with db_session:
            # Delete Paris - should remove paris from d1 and d2, but keep the districts
            study_dao.delete_area("paris")

        with db_session:
            # All districts should still exist
            assert dao.district_exists("d1")
            assert dao.district_exists("d2")
            assert dao.district_exists("d3")

            # Paris should be removed from add_areas
            d1 = dao.get_district("d1")
            assert "paris" not in d1.add_areas

            d2 = dao.get_district("d2")
            assert "paris" not in d2.add_areas
            assert "london" in d2.add_areas

            d3 = dao.get_district("d3")
            assert d3.add_areas == ["london"]

    def test_delete_area_removes_area_from_subtract_areas(
        self, db_session: Session, dao: DatabaseDistrictDao, study_dao: DatabaseStudyDao
    ) -> None:
        """When an area is deleted, it should be removed from subtract_areas of districts."""
        with db_session:
            study_dao.save_area("Paris")
            db_session.commit()

        with db_session:
            dao.save_district(
                District(
                    id="d1",
                    name="District 1",
                    apply_filter=DistrictApplyFilter.add_all,
                    subtract_areas=["paris"],
                )
            )
            db_session.commit()

        with db_session:
            assert dao.district_exists("d1")

        with db_session:
            study_dao.delete_area("paris")

        with db_session:
            # District should still exist
            assert dao.district_exists("d1")
            # Paris should be removed from subtract_areas
            d1 = dao.get_district("d1")
            assert "paris" not in d1.subtract_areas

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

import pytest

from antarest.core.exceptions import AreaNotFound, DistrictConfigNotFound
from antarest.study.business.model.district_model import District, DistrictApplyFilter
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


class TestDatabaseDistrictDao:
    def test_save_district_creates_district(self, dao: DatabaseStudyDao) -> None:
        district = District(id="d1", name="District 1", comments="test")
        dao.save_district(district)

        result = dao.get_district("d1")
        assert result.id == "d1"
        assert result.name == "District 1"
        assert result.output is True
        assert result.comments == "test"

    def test_save_district_with_areas(self, dao: DatabaseStudyDao) -> None:
        dao.save_area("Paris")
        dao.save_area("London")

        district = District(id="d1", name="District 1", add_areas=["paris", "london"])
        dao.save_district(district)

        result = dao.get_district("d1")
        assert set(result.add_areas) == {"paris", "london"}

    def test_save_district_raises_on_invalid_area(self, dao: DatabaseStudyDao) -> None:
        district = District(id="d1", name="District 1", add_areas=["nonexistent"])
        with pytest.raises(AreaNotFound):
            dao.save_district(district)

    def test_save_district_overwrites_existing(self, dao: DatabaseStudyDao) -> None:
        dao.save_district(District(id="d1", name="District 1", comments="v1"))
        dao.save_district(District(id="d1", name="District 1", comments="v2"))

        result = dao.get_district("d1")
        assert result.comments == "v2"

    def test_remove_district(self, dao: DatabaseStudyDao) -> None:
        dao.save_district(District(id="d1", name="District 1"))
        dao.remove_district("d1")
        assert not dao.district_exists("d1")

    def test_get_districts_returns_all(self, dao: DatabaseStudyDao) -> None:
        dao.save_district(District(id="d1", name="District 1"))
        dao.save_district(District(id="d2", name="District 2"))

        districts = dao.get_districts()
        assert len(districts) == 2
        assert {d.id for d in districts} == {"d1", "d2"}

    def test_get_district_raises_if_not_found(self, dao: DatabaseStudyDao) -> None:
        with pytest.raises(DistrictConfigNotFound):
            dao.get_district("nonexistent")

    def test_district_exists(self, dao: DatabaseStudyDao) -> None:
        assert not dao.district_exists("d1")
        dao.save_district(District(id="d1", name="District 1"))

        assert dao.district_exists("d1")

    def test_save_district_with_apply_filter(self, dao: DatabaseStudyDao) -> None:
        dao.save_area("Paris")

        district = District(
            id="d1",
            name="District 1",
            apply_filter=DistrictApplyFilter.add_all,
            subtract_areas=["paris"],
        )
        dao.save_district(district)

        result = dao.get_district("d1")
        assert result.apply_filter == DistrictApplyFilter.add_all
        assert result.subtract_areas == ["paris"]

    def test_delete_area_removes_area_from_districts(self, dao: DatabaseStudyDao) -> None:
        dao.save_area("Paris")
        dao.save_area("London")

        dao.save_district(District(id="d1", name="District 1", add_areas=["paris"]))
        dao.save_district(District(id="d2", name="District 2", add_areas=["paris", "london"]))
        dao.save_district(District(id="d3", name="District 3", add_areas=["london"]))

        dao.delete_area("paris")

        assert dao.district_exists("d1")
        assert dao.district_exists("d2")
        assert dao.district_exists("d3")

        d1 = dao.get_district("d1")
        assert "paris" not in d1.add_areas

        d2 = dao.get_district("d2")
        assert "paris" not in d2.add_areas
        assert "london" in d2.add_areas

        d3 = dao.get_district("d3")
        assert d3.add_areas == ["london"]

    def test_delete_area_removes_area_from_subtract_areas(self, dao: DatabaseStudyDao) -> None:
        dao.save_area("Paris")

        dao.save_district(
            District(
                id="d1",
                name="District 1",
                apply_filter=DistrictApplyFilter.add_all,
                subtract_areas=["paris"],
            )
        )

        assert dao.district_exists("d1")

        dao.delete_area("paris")

        assert dao.district_exists("d1")

        d1 = dao.get_district("d1")
        assert "paris" not in d1.subtract_areas

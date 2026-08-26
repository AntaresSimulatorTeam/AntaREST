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
import pytest

from antarest.core.exceptions import AreaNotFound, ReserveDefinitionsNotFound
from antarest.study.business.model.reserve_certification_model import StorageReserveCertification
from antarest.study.business.model.reserve_definition_model import ReserveDefinition, ReserveType
from antarest.study.dao.api.study_dao import StudyDao
from tests.study.dao.utils import save_area


def _set_up(dao: StudyDao) -> None:
    # Create 1 area with 3 reserves. Hydro needs no asset: an area owns exactly one long-term storage.
    save_area(dao, "fr")
    dao.save_reserve_definitions(
        {"fr": [ReserveDefinition(name=name, type=ReserveType.UP) for name in ["r1", "r2", "r3"]]}
    )


def test_save_and_retrieve(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)

    certification = StorageReserveCertification(max_release=100.0, max_store=80.0, participation_cost=1.5)
    dao.save_hydro_reserve_certifications({"fr": {"r1": certification}})

    assert dao.get_hydro_reserve_certifications("fr") == {"r1": certification}
    assert dao.get_all_hydro_reserve_certifications() == {"fr": {"r1": certification}}


def test_defaults_are_zero(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)

    dao.save_hydro_reserve_certifications({"fr": {"r1": StorageReserveCertification()}})

    fetched = dao.get_hydro_reserve_certifications("fr")["r1"]
    assert fetched.max_release == 0.0
    assert fetched.max_store == 0.0
    assert fetched.participation_cost == 0.0


def test_save_replaces_the_whole_area(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)

    dao.save_hydro_reserve_certifications(
        {"fr": {"r1": StorageReserveCertification(max_release=1.0), "r2": StorageReserveCertification(max_release=2.0)}}
    )
    # `r1` is absent from the new data, so its certification must be removed
    dao.save_hydro_reserve_certifications({"fr": {"r2": StorageReserveCertification(max_release=3.0)}})

    assert dao.get_hydro_reserve_certifications("fr") == {"r2": StorageReserveCertification(max_release=3.0)}


def test_get_on_area_without_certification(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)

    assert dao.get_hydro_reserve_certifications("fr") == {}
    assert dao.get_all_hydro_reserve_certifications() == {}


def test_save_raises_on_unknown_area(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)

    with pytest.raises(AreaNotFound):
        dao.save_hydro_reserve_certifications({"unknown": {"r1": StorageReserveCertification()}})


def test_save_raises_on_unknown_reserve(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)

    with pytest.raises(ReserveDefinitionsNotFound):
        dao.save_hydro_reserve_certifications({"fr": {"unknown": StorageReserveCertification()}})


def test_deleting_a_reserve_cascades_on_certifications(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)

    certification = StorageReserveCertification(max_release=10.0)
    dao.save_hydro_reserve_certifications({"fr": {"r1": certification, "r2": certification}})

    dao.delete_reserve_definitions("fr", ["r1"])

    assert dao.get_hydro_reserve_certifications("fr") == {"r2": certification}


def test_deleting_an_area_cascades_on_certifications(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)
    dao.save_hydro_reserve_certifications({"fr": {"r1": StorageReserveCertification()}})

    dao.delete_area("fr")

    assert dao.get_all_hydro_reserve_certifications() == {}


def test_certifications_of_areas_are_independent(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)
    save_area(dao, "de")
    dao.save_reserve_definitions({"de": [ReserveDefinition(name="r1", type=ReserveType.UP)]})

    fr_certification = StorageReserveCertification(max_release=1.0)
    de_certification = StorageReserveCertification(max_release=2.0)
    dao.save_hydro_reserve_certifications({"fr": {"r1": fr_certification}})
    dao.save_hydro_reserve_certifications({"de": {"r1": de_certification}})

    # Saving `de` must not have touched `fr`
    assert dao.get_all_hydro_reserve_certifications() == {
        "fr": {"r1": fr_certification},
        "de": {"r1": de_certification},
    }


def test_save_on_an_area_leaves_the_others_untouched(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)
    save_area(dao, "de")
    dao.save_reserve_definitions({"de": [ReserveDefinition(name="r1", type=ReserveType.UP)]})
    dao.save_hydro_reserve_certifications({"de": {"r1": StorageReserveCertification(max_store=5.0)}})

    # `de` is absent from the given data, so its certifications must not be modified.
    dao.save_hydro_reserve_certifications({"fr": {"r1": StorageReserveCertification()}})

    assert dao.get_hydro_reserve_certifications("de") == {"r1": StorageReserveCertification(max_store=5.0)}

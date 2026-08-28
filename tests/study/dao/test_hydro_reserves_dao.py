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

from antarest.core.exceptions import (
    AreaNotFound,
    ReserveCertificationNotFound,
    ReserveDefinitionNotFound,
    ReserveDefinitionsNotFound,
)
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


##########################
# Symmetries
##########################


def _certify(dao: StudyDao, *reserve_ids: str) -> None:
    dao.save_hydro_reserve_certifications({"fr": {r: StorageReserveCertification() for r in reserve_ids}})


def test_save_and_retrieve_symmetries(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)
    _certify(dao, "r1", "r2")

    dao.save_hydro_reserve_symmetries({"fr": [["r1", "r2"]]})

    assert dao.get_hydro_reserve_symmetries("fr") == [["r1", "r2"]]
    assert dao.get_all_hydro_reserve_symmetries() == {"fr": [["r1", "r2"]]}


def test_get_symmetries_on_area_without_any(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)

    assert dao.get_hydro_reserve_symmetries("fr") == []
    assert dao.get_all_hydro_reserve_symmetries() == {}


def test_save_symmetries_replaces_the_whole_area(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)
    _certify(dao, "r1", "r2", "r3")
    dao.save_hydro_reserve_symmetries({"fr": [["r1", "r2"]]})

    dao.save_hydro_reserve_symmetries({"fr": [["r2", "r3"]]})

    assert dao.get_hydro_reserve_symmetries("fr") == [["r2", "r3"]]


def test_saving_empty_symmetries_clears_them(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)
    _certify(dao, "r1", "r2")
    dao.save_hydro_reserve_symmetries({"fr": [["r1", "r2"]]})

    dao.save_hydro_reserve_symmetries({"fr": []})

    assert dao.get_hydro_reserve_symmetries("fr") == []


def test_save_symmetries_raises_on_uncertified_reserve(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)
    # Only `r1` is certified, so a symmetry naming `r2` is invalid.
    _certify(dao, "r1")

    with pytest.raises(ReserveCertificationNotFound):
        dao.save_hydro_reserve_symmetries({"fr": [["r1", "r2"]]})


def test_save_symmetries_raises_on_unknown_reserve(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)
    _certify(dao, "r1")

    with pytest.raises(ReserveDefinitionNotFound):
        dao.save_hydro_reserve_symmetries({"fr": [["r1", "unknown"]]})


def test_save_symmetries_raises_on_unknown_area(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)

    with pytest.raises(AreaNotFound):
        dao.save_hydro_reserve_symmetries({"unknown": [["r1", "r2"]]})


def test_deleting_a_reserve_cascades_on_symmetries(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)
    _certify(dao, "r1", "r2", "r3")
    dao.save_hydro_reserve_symmetries({"fr": [["r1", "r2"], ["r2", "r3"]]})

    dao.delete_reserve_definitions("fr", ["r1"])

    # ["r1", "r2"] is left with a single reserve so it is dropped; ["r2", "r3"] survives.
    assert dao.get_hydro_reserve_symmetries("fr") == [["r2", "r3"]]


def test_removing_a_certification_cascades_on_symmetries(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)
    _certify(dao, "r1", "r2", "r3")
    dao.save_hydro_reserve_symmetries({"fr": [["r1", "r2"], ["r2", "r3"]]})

    # `r1` loses its certification, so any symmetry relying on it must be cleaned up.
    _certify(dao, "r2", "r3")

    assert dao.get_hydro_reserve_symmetries("fr") == [["r2", "r3"]]


def test_deleting_an_area_cascades_on_symmetries(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)
    _certify(dao, "r1", "r2")
    dao.save_hydro_reserve_symmetries({"fr": [["r1", "r2"]]})

    dao.delete_area("fr")

    assert dao.get_all_hydro_reserve_symmetries() == {}


def test_symmetries_of_areas_are_independent(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)
    save_area(dao, "de")
    dao.save_reserve_definitions({"de": [ReserveDefinition(name=name, type=ReserveType.UP) for name in ["r1", "r2"]]})
    dao.save_hydro_reserve_certifications(
        {"de": {"r1": StorageReserveCertification(), "r2": StorageReserveCertification()}}
    )
    _certify(dao, "r1", "r2")

    dao.save_hydro_reserve_symmetries({"de": [["r1", "r2"]]})
    assert dao.get_all_hydro_reserve_symmetries() == {"de": [["r1", "r2"]]}

    dao.save_hydro_reserve_symmetries({"fr": [["r1", "r2"]]})
    assert dao.get_all_hydro_reserve_symmetries() == {"fr": [["r1", "r2"]], "de": [["r1", "r2"]]}

    dao.save_hydro_reserve_symmetries({"de": []})
    assert dao.get_all_hydro_reserve_symmetries() == {"fr": [["r1", "r2"]]}

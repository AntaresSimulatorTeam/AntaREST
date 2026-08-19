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


from antarest.study.business.model.area_properties_model import AreaProperties
from antarest.study.business.model.reserve_certification_model import StorageReserveCertification
from antarest.study.business.model.reserve_definition_model import ReserveDefinition, ReserveType
from antarest.study.business.model.sts_model import STStorage, initialize_st_storage
from antarest.study.dao.api.study_dao import StudyDao


def _set_up(dao: StudyDao) -> None:
    # Create 1 area with 2 short-term storages and 4 reserves
    dao.save_areas_with_properties({"fr": AreaProperties()})
    sts1 = STStorage(name="sts1")
    sts2 = STStorage(name="sts2")
    initialize_st_storage(sts1, dao.get_version())
    initialize_st_storage(sts2, dao.get_version())
    dao.save_st_storages({"fr": [sts1, sts2]})
    reserves = []
    for reserve_name in ["r1", "r2", "r3", "r4"]:
        reserves.append(ReserveDefinition(name=reserve_name, type=ReserveType.DOWN))
    dao.save_reserve_definitions({"fr": reserves})


def test_symmetries_and_certifications_do_not_overwrite_each_other(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)

    # A storage can only be symmetric on reserves it is certified for, so certify everything sts1 needs first.
    dao.save_st_storage_reserve_certifications(
        {
            "fr": {
                "r1": {"sts1": StorageReserveCertification(), "sts2": StorageReserveCertification()},
                "r2": {"sts1": StorageReserveCertification(), "sts2": StorageReserveCertification()},
                "r3": {"sts1": StorageReserveCertification(), "sts2": StorageReserveCertification()},
                "r4": {"sts1": StorageReserveCertification()},
            }
        }
    )

    # Save 2 symmetries. Then 1 certification. Ensures the certification writing didn't affect the symmetries.
    dao.save_st_storage_reserve_symmetries({"fr": {"sts1": [["r1", "r2"], ["r3", "r4"]]}})
    dao.save_st_storage_reserve_certifications(
        {
            "fr": {
                "r1": {"sts1": StorageReserveCertification(), "sts2": StorageReserveCertification()},
                "r2": {"sts2": StorageReserveCertification()},
                "r3": {"sts2": StorageReserveCertification()},
            }
        }
    )

    assert dao.get_st_storage_reserve_symmetries("fr") == {"sts1": [["r1", "r2"], ["r3", "r4"]]}
    assert dao.get_st_storage_reserve_certifications("fr") == {
        "r1": {"sts1": StorageReserveCertification(), "sts2": StorageReserveCertification()},
        "r2": {"sts2": StorageReserveCertification()},
        "r3": {"sts2": StorageReserveCertification()},
    }

    # Save a new symmetry. Ensures the symmetry writing didn't affect the certification.
    dao.save_st_storage_reserve_symmetries({"fr": {"sts2": [["r1", "r2", "r3"]]}})

    assert dao.get_st_storage_reserve_certifications("fr") == {
        "r1": {"sts1": StorageReserveCertification(), "sts2": StorageReserveCertification()},
        "r2": {"sts2": StorageReserveCertification()},
        "r3": {"sts2": StorageReserveCertification()},
    }
    # The symmetry should also be overwritten by the new value.
    assert dao.get_st_storage_reserve_symmetries("fr") == {"sts2": [["r1", "r2", "r3"]]}

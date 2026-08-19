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
from antarest.study.business.model.reserve_certification_model import ThermalReserveCertification
from antarest.study.business.model.reserve_definition_model import ReserveDefinition, ReserveType
from antarest.study.business.model.thermal_cluster_model import ThermalCluster, initialize_thermal_cluster
from antarest.study.dao.api.study_dao import StudyDao


def _set_up(dao: StudyDao) -> None:
    # Create 1 area with 2 thermal clusters and 4 reserves
    dao.save_areas_with_properties({"fr": AreaProperties()})
    th1 = ThermalCluster(name="th1")
    th2 = ThermalCluster(name="th2")
    initialize_thermal_cluster(th1, dao.get_version())
    initialize_thermal_cluster(th2, dao.get_version())
    dao.save_thermals({"fr": [th1, th2]})
    reserves = []
    for reserve_name in ["r1", "r2", "r3", "r4"]:
        reserves.append(ReserveDefinition(name=reserve_name, type=ReserveType.DOWN))
    dao.save_reserve_definitions({"fr": reserves})


def test_symmetries_and_certifications_do_not_overwrite_each_other(dao_10_2: StudyDao) -> None:
    dao = dao_10_2
    _set_up(dao)

    # A cluster can only be symmetric on reserves it is certified for, so certify both clusters first.
    certification = ThermalReserveCertification()
    certifications = {
        reserve_id: {"th1": certification, "th2": certification} for reserve_id in ["r1", "r2", "r3", "r4"]
    }
    dao.save_thermal_reserve_certifications({"fr": certifications})

    # Save 2 symmetries. Then rewrite the certifications. Ensures the certification writing didn't affect the
    # symmetries.
    dao.save_thermal_reserve_symmetries({"fr": {"th1": [["r1", "r2"], ["r3", "r4"]]}})
    dao.save_thermal_reserve_certifications({"fr": certifications})

    assert dao.get_thermal_reserve_symmetries("fr") == {"th1": [["r1", "r2"], ["r3", "r4"]]}
    assert dao.get_thermal_reserve_certifications("fr") == certifications

    # Save a new symmetry. Ensures the symmetry writing didn't affect the certifications.
    dao.save_thermal_reserve_symmetries({"fr": {"th2": [["r1", "r2", "r3"]]}})

    assert dao.get_thermal_reserve_certifications("fr") == certifications
    # The symmetry should also be overwritten by the new value.
    assert dao.get_thermal_reserve_symmetries("fr") == {"th2": [["r1", "r2", "r3"]]}


def test_deleting_the_last_reserves_removes_their_symmetries(dao_10_2: StudyDao) -> None:
    # Deleting a reserve cascades on the certifications and on the symmetries referencing it.
    dao = dao_10_2
    _set_up(dao)
    certification = ThermalReserveCertification()
    dao.save_thermal_reserve_certifications({"fr": {"r1": {"th1": certification}, "r2": {"th1": certification}}})
    dao.save_thermal_reserve_symmetries({"fr": {"th1": [["r1", "r2"]]}})

    # Deleting every reserve of the area leaves it without any certification and symmetries.
    dao.delete_reserve_definitions("fr", ["r1", "r2"])

    certifications = dao.get_all_thermal_reserve_certifications()
    assert certifications == {}

    symmetries = dao.get_thermal_reserve_symmetries("fr")
    assert symmetries == {}
